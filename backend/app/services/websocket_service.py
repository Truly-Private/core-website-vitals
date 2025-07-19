"""
WebSocket service for real-time communication.
Handles WebSocket connections and broadcasting updates to connected clients.
"""
import json
import asyncio
import logging
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    """WebSocket message types."""
    ANALYSIS_UPDATE = "analysis_update"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_FAILED = "analysis_failed"
    NOTIFICATION = "notification"
    USER_ACTIVITY = "user_activity"
    HEARTBEAT = "heartbeat"
    ERROR = "error"

class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    analysis_id: Optional[str] = None

class ConnectionManager:
    """
    Manages WebSocket connections and handles message broadcasting.
    """
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Store analysis subscribers
        self.analysis_subscribers: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, metadata: Dict[str, Any] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Initialize user connections if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        # Add connection
        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            'user_id': user_id,
            'connected_at': datetime.utcnow(),
            'last_heartbeat': datetime.utcnow(),
            **(metadata or {})
        }
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message({
            'type': MessageType.NOTIFICATION,
            'data': {
                'title': 'Connected',
                'message': 'Real-time updates enabled',
                'type': 'info'
            },
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
        
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata[websocket]
            user_id = metadata['user_id']
            
            # Remove from active connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove from analysis subscribers
            for analysis_id, subscribers in self.analysis_subscribers.items():
                subscribers.discard(websocket)
            
            # Clean up empty subscriber lists
            self.analysis_subscribers = {
                k: v for k, v in self.analysis_subscribers.items() if v
            }
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to send message to websocket: {e}")
            await self.disconnect(websocket)
    
    async def broadcast_to_user(self, message: Dict[str, Any], user_id: str):
        """Broadcast a message to all connections for a specific user."""
        if user_id in self.active_connections:
            connections = self.active_connections[user_id].copy()
            for connection in connections:
                await self.send_personal_message(message, connection)
    
    async def broadcast_to_analysis_subscribers(self, message: Dict[str, Any], analysis_id: str):
        """Broadcast a message to all subscribers of a specific analysis."""
        if analysis_id in self.analysis_subscribers:
            subscribers = self.analysis_subscribers[analysis_id].copy()
            for subscriber in subscribers:
                await self.send_personal_message(message, subscriber)
    
    async def subscribe_to_analysis(self, websocket: WebSocket, analysis_id: str):
        """Subscribe a WebSocket to analysis updates."""
        if analysis_id not in self.analysis_subscribers:
            self.analysis_subscribers[analysis_id] = set()
        
        self.analysis_subscribers[analysis_id].add(websocket)
        
        # Send confirmation
        await self.send_personal_message({
            'type': MessageType.NOTIFICATION,
            'data': {
                'title': 'Subscribed',
                'message': f'Subscribed to analysis {analysis_id[:8]}...',
                'type': 'info'
            },
            'timestamp': datetime.utcnow().isoformat()
        }, websocket)
    
    async def unsubscribe_from_analysis(self, websocket: WebSocket, analysis_id: str):
        """Unsubscribe a WebSocket from analysis updates."""
        if analysis_id in self.analysis_subscribers:
            self.analysis_subscribers[analysis_id].discard(websocket)
            if not self.analysis_subscribers[analysis_id]:
                del self.analysis_subscribers[analysis_id]
    
    async def send_analysis_update(self, analysis_id: str, user_id: str, update_data: Dict[str, Any]):
        """Send analysis update to subscribers and user."""
        message = {
            'type': MessageType.ANALYSIS_UPDATE,
            'data': update_data,
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_id': analysis_id
        }
        
        # Send to analysis subscribers
        await self.broadcast_to_analysis_subscribers(message, analysis_id)
        
        # Send to user if they're not already subscribed
        await self.broadcast_to_user(message, user_id)
    
    async def send_analysis_progress(self, analysis_id: str, user_id: str, progress: float, stage: str, details: str = None):
        """Send analysis progress update."""
        message = {
            'type': MessageType.ANALYSIS_PROGRESS,
            'data': {
                'analysis_id': analysis_id,
                'progress': progress,
                'stage': stage,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_id': analysis_id
        }
        
        await self.broadcast_to_analysis_subscribers(message, analysis_id)
        await self.broadcast_to_user(message, user_id)
    
    async def send_analysis_complete(self, analysis_id: str, user_id: str, results: Dict[str, Any]):
        """Send analysis completion notification."""
        message = {
            'type': MessageType.ANALYSIS_COMPLETE,
            'data': {
                'analysis_id': analysis_id,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_id': analysis_id
        }
        
        await self.broadcast_to_analysis_subscribers(message, analysis_id)
        await self.broadcast_to_user(message, user_id)
    
    async def send_analysis_failed(self, analysis_id: str, user_id: str, error: str):
        """Send analysis failure notification."""
        message = {
            'type': MessageType.ANALYSIS_FAILED,
            'data': {
                'analysis_id': analysis_id,
                'error': error,
                'timestamp': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_id': analysis_id
        }
        
        await self.broadcast_to_analysis_subscribers(message, analysis_id)
        await self.broadcast_to_user(message, user_id)
    
    async def send_notification(self, user_id: str, title: str, message: str, notification_type: str = 'info'):
        """Send a notification to a user."""
        message_data = {
            'type': MessageType.NOTIFICATION,
            'data': {
                'title': title,
                'message': message,
                'type': notification_type,
                'timestamp': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_user(message_data, user_id)
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == MessageType.HEARTBEAT:
                # Update heartbeat timestamp
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]['last_heartbeat'] = datetime.utcnow()
                
                # Send heartbeat response
                await self.send_personal_message({
                    'type': MessageType.HEARTBEAT,
                    'data': {'timestamp': datetime.utcnow().isoformat()},
                    'timestamp': datetime.utcnow().isoformat()
                }, websocket)
                
            elif message_type == 'subscribe_analysis':
                analysis_id = data.get('analysis_id')
                if analysis_id:
                    await self.subscribe_to_analysis(websocket, analysis_id)
                    
            elif message_type == 'unsubscribe_analysis':
                analysis_id = data.get('analysis_id')
                if analysis_id:
                    await self.unsubscribe_from_analysis(websocket, analysis_id)
                    
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
            await self.send_personal_message({
                'type': MessageType.ERROR,
                'data': {'error': 'Invalid JSON message'},
                'timestamp': datetime.utcnow().isoformat()
            }, websocket)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_personal_message({
                'type': MessageType.ERROR,
                'data': {'error': 'Message processing error'},
                'timestamp': datetime.utcnow().isoformat()
            }, websocket)
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections based on heartbeat."""
        current_time = datetime.utcnow()
        stale_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            last_heartbeat = metadata.get('last_heartbeat')
            if last_heartbeat and (current_time - last_heartbeat).total_seconds() > 300:  # 5 minutes
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            await self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        total_users = len(self.active_connections)
        total_analysis_subscriptions = sum(len(subscribers) for subscribers in self.analysis_subscribers.values())
        
        return {
            'total_connections': total_connections,
            'total_users': total_users,
            'total_analysis_subscriptions': total_analysis_subscriptions,
            'active_analyses': len(self.analysis_subscribers)
        }

# Global connection manager instance
connection_manager = ConnectionManager()

# Background task for cleanup
async def cleanup_task():
    """Background task to clean up stale connections."""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        try:
            await connection_manager.cleanup_stale_connections()
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")

class WebSocketService:
    """
    Service class for WebSocket operations.
    """
    
    def __init__(self):
        self.connection_manager = connection_manager
    
    async def connect_user(self, websocket: WebSocket, user_id: str, metadata: Dict[str, Any] = None):
        """Connect a user via WebSocket."""
        await self.connection_manager.connect(websocket, user_id, metadata)
    
    async def disconnect_user(self, websocket: WebSocket):
        """Disconnect a user's WebSocket."""
        await self.connection_manager.disconnect(websocket)
    
    async def send_analysis_update(self, analysis_id: str, user_id: str, update_data: Dict[str, Any]):
        """Send analysis update to connected clients."""
        await self.connection_manager.send_analysis_update(analysis_id, user_id, update_data)
    
    async def send_analysis_progress(self, analysis_id: str, user_id: str, progress: float, stage: str, details: str = None):
        """Send analysis progress update."""
        await self.connection_manager.send_analysis_progress(analysis_id, user_id, progress, stage, details)
    
    async def send_analysis_complete(self, analysis_id: str, user_id: str, results: Dict[str, Any]):
        """Send analysis completion notification."""
        await self.connection_manager.send_analysis_complete(analysis_id, user_id, results)
    
    async def send_analysis_failed(self, analysis_id: str, user_id: str, error: str):
        """Send analysis failure notification."""
        await self.connection_manager.send_analysis_failed(analysis_id, user_id, error)
    
    async def send_notification(self, user_id: str, title: str, message: str, notification_type: str = 'info'):
        """Send a notification to a user."""
        await self.connection_manager.send_notification(user_id, title, message, notification_type)
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket message."""
        await self.connection_manager.handle_message(websocket, message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return self.connection_manager.get_connection_stats()

# Global service instance
websocket_service = WebSocketService()