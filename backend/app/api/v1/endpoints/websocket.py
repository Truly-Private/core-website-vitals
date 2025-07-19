"""
WebSocket API endpoints for real-time communication.
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from app.services.websocket_service import websocket_service
from app.services.auth_service import get_current_user_websocket, get_current_user
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time communication.
    
    Args:
        websocket: WebSocket connection
        token: JWT access token for authentication
    """
    try:
        # Decode token and get user info
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user")
            return
        
        # Connect user
        await websocket_service.connect_user(websocket, user_id, {
            'user_agent': websocket.headers.get('user-agent', 'Unknown'),
            'ip_address': websocket.client.host if websocket.client else 'Unknown'
        })
        
        try:
            # Handle incoming messages
            while True:
                message = await websocket.receive_text()
                await websocket_service.handle_message(websocket, message)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
        finally:
            await websocket_service.disconnect_user(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Server error")

@router.get("/stats")
async def get_websocket_stats(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get WebSocket connection statistics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Connection statistics
    """
    # Only allow admin users to see stats
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return websocket_service.get_stats()

@router.post("/test-notification")
async def test_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    current_user: dict = Depends(get_current_user)
):
    """
    Test endpoint to send a notification to the current user.
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
        current_user: Current authenticated user
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user"
        )
    
    await websocket_service.send_notification(user_id, title, message, notification_type)
    
    return {"message": "Notification sent successfully"}

@router.post("/broadcast-notification")
async def broadcast_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    current_user: dict = Depends(get_current_user)
):
    """
    Broadcast a notification to all connected users (admin only).
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
        current_user: Current authenticated user
    """
    # Only allow admin users to broadcast
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get all connected users and send notification
    stats = websocket_service.get_stats()
    
    # Note: This is a simplified broadcast. In a real implementation,
    # you'd want to iterate through all connected users
    await websocket_service.send_notification("all", title, message, notification_type)
    
    return {
        "message": "Notification broadcasted successfully",
        "recipients": stats["total_users"]
    }