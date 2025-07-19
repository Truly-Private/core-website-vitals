"""
Database service layer for Core Website Vitals.
Provides comprehensive CRUD operations and database management for Supabase.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID, uuid4
from supabase import Client
from fastapi import HTTPException, status
from app.models.database import DatabaseManager, ProfilesTable, AnalysisTasksTable
from app.models.schemas import (
    AnalysisStatus, 
    AnalysisType, 
    SubscriptionTier,
    UserResponse,
    AnalysisTaskResponse,
    DashboardSummaryResponse,
    DashboardTrendsResponse,
    DashboardMetricsResponse
)
import structlog

logger = structlog.get_logger(__name__)


class SupabaseService:
    """
    Comprehensive service layer for Supabase database operations.
    Provides CRUD operations, error handling, and connection management.
    """
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.db_manager = DatabaseManager(supabase_client)
        self.profiles = ProfilesTable(supabase_client)
        self.analysis_tasks = AnalysisTasksTable(supabase_client)
    
    # Database Health and Connection Management
    async def health_check(self) -> Dict[str, Any]:
        """
        Check database health and connection status.
        
        Returns:
            Database health status
        """
        try:
            is_healthy = await self.db_manager.health_check()
            
            return {
                "healthy": is_healthy,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "supabase",
                "connection_status": "connected" if is_healthy else "disconnected"
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "healthy": False,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "supabase",
                "connection_status": "error",
                "error": str(e)
            }
    
    # User Profile Operations
    async def create_user_profile(
        self, 
        user_id: str, 
        email: str, 
        full_name: Optional[str] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user profile.
        
        Args:
            user_id: User ID from Supabase Auth
            email: User email address
            full_name: User's full name
            subscription_tier: User's subscription tier
            
        Returns:
            Created profile data or None if creation failed
        """
        try:
            profile_data = await self.profiles.create_profile(
                user_id=user_id,
                email=email,
                full_name=full_name
            )
            
            if profile_data:
                logger.info("User profile created successfully", 
                           user_id=user_id, email=email)
            
            return profile_data
            
        except Exception as e:
            logger.error("Failed to create user profile", 
                        user_id=user_id, email=email, error=str(e))
            return None
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile data or None if not found
        """
        try:
            profile_data = await self.profiles.get_profile(user_id)
            return profile_data
            
        except Exception as e:
            logger.error("Failed to get user profile", 
                        user_id=user_id, error=str(e))
            return None
    
    async def update_user_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            updates: Fields to update
            
        Returns:
            Updated profile data or None if update failed
        """
        try:
            updated_profile = await self.profiles.update_profile(user_id, updates)
            
            if updated_profile:
                logger.info("User profile updated successfully", 
                           user_id=user_id, updates=updates)
            
            return updated_profile
            
        except Exception as e:
            logger.error("Failed to update user profile", 
                        user_id=user_id, updates=updates, error=str(e))
            return None
    
    async def delete_user_profile(self, user_id: str) -> bool:
        """
        Delete user profile and all associated data.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deletion successful
        """
        try:
            deleted = await self.profiles.delete_profile(user_id)
            
            if deleted:
                logger.info("User profile deleted successfully", user_id=user_id)
            
            return deleted
            
        except Exception as e:
            logger.error("Failed to delete user profile", 
                        user_id=user_id, error=str(e))
            return False
    
    # Analysis Task Operations
    async def create_analysis_task(
        self, 
        user_id: str, 
        url: str, 
        analysis_type: AnalysisType = AnalysisType.FULL_SEO,
        celery_task_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new analysis task.
        
        Args:
            user_id: User ID
            url: URL to analyze
            analysis_type: Type of analysis
            celery_task_id: Celery task ID for tracking
            
        Returns:
            Created analysis task data or None if creation failed
        """
        try:
            task_data = await self.analysis_tasks.create_analysis_task(
                user_id=user_id,
                url=url,
                analysis_type=analysis_type
            )
            
            if task_data and celery_task_id:
                # Update with celery task ID
                await self.analysis_tasks.update_analysis_task(
                    task_data["id"], 
                    {"celery_task_id": celery_task_id}
                )
                task_data["celery_task_id"] = celery_task_id
            
            if task_data:
                logger.info("Analysis task created successfully", 
                           user_id=user_id, url=url, task_id=task_data["id"])
            
            return task_data
            
        except Exception as e:
            logger.error("Failed to create analysis task", 
                        user_id=user_id, url=url, error=str(e))
            return None
    
    async def get_analysis_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Analysis task data or None if not found
        """
        try:
            task_data = await self.analysis_tasks.get_analysis_task(task_id)
            return task_data
            
        except Exception as e:
            logger.error("Failed to get analysis task", 
                        task_id=task_id, error=str(e))
            return None
    
    async def get_user_analysis_tasks(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        status: Optional[AnalysisStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's analysis tasks with pagination.
        
        Args:
            user_id: User ID
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            status: Optional status filter
            
        Returns:
            List of analysis tasks
        """
        try:
            tasks = await self.analysis_tasks.get_user_analysis_tasks(
                user_id=user_id,
                limit=limit,
                offset=offset,
                status=status
            )
            
            return tasks
            
        except Exception as e:
            logger.error("Failed to get user analysis tasks", 
                        user_id=user_id, error=str(e))
            return []
    
    async def update_analysis_task(
        self, 
        task_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update analysis task.
        
        Args:
            task_id: Task ID
            updates: Fields to update
            
        Returns:
            Updated task data or None if update failed
        """
        try:
            updated_task = await self.analysis_tasks.update_analysis_task(
                task_id, updates
            )
            
            if updated_task:
                logger.info("Analysis task updated successfully", 
                           task_id=task_id, updates=updates)
            
            return updated_task
            
        except Exception as e:
            logger.error("Failed to update analysis task", 
                        task_id=task_id, updates=updates, error=str(e))
            return None
    
    async def set_analysis_task_status(
        self, 
        task_id: str, 
        status: AnalysisStatus,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Set analysis task status.
        
        Args:
            task_id: Task ID
            status: New status
            error_message: Error message if status is FAILED
            
        Returns:
            Updated task data or None if update failed
        """
        try:
            updated_task = await self.analysis_tasks.set_task_status(
                task_id=task_id,
                status=status,
                error_message=error_message
            )
            
            if updated_task:
                logger.info("Analysis task status updated", 
                           task_id=task_id, status=status)
            
            return updated_task
            
        except Exception as e:
            logger.error("Failed to set analysis task status", 
                        task_id=task_id, status=status, error=str(e))
            return None
    
    async def set_analysis_task_results(
        self, 
        task_id: str, 
        results: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Set analysis task results.
        
        Args:
            task_id: Task ID
            results: Analysis results
            
        Returns:
            Updated task data or None if update failed
        """
        try:
            updated_task = await self.analysis_tasks.set_task_results(
                task_id=task_id,
                results=results
            )
            
            if updated_task:
                logger.info("Analysis task results set successfully", 
                           task_id=task_id)
            
            return updated_task
            
        except Exception as e:
            logger.error("Failed to set analysis task results", 
                        task_id=task_id, error=str(e))
            return None
    
    async def delete_analysis_task(self, task_id: str) -> bool:
        """
        Delete analysis task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if deletion successful
        """
        try:
            deleted = await self.analysis_tasks.delete_analysis_task(task_id)
            
            if deleted:
                logger.info("Analysis task deleted successfully", task_id=task_id)
            
            return deleted
            
        except Exception as e:
            logger.error("Failed to delete analysis task", 
                        task_id=task_id, error=str(e))
            return False
    
    # Dashboard and Analytics Operations
    async def get_user_dashboard_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get dashboard summary for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dashboard summary data or None if failed
        """
        try:
            summary = await self.analysis_tasks.get_user_analysis_summary(user_id)
            
            if not summary:
                return {
                    "total_analyses": 0,
                    "successful_analyses": 0,
                    "failed_analyses": 0,
                    "pending_analyses": 0,
                    "average_score": 0.0,
                    "average_analysis_time": 0.0,
                    "last_analysis_date": None
                }
            
            # Calculate additional metrics
            total_analyses = summary["total_analyses"]
            successful_analyses = summary["successful_analyses"]
            
            # Get successful tasks for score calculation
            successful_tasks = await self.analysis_tasks.get_user_analysis_tasks(
                user_id=user_id,
                status=AnalysisStatus.SUCCESS,
                limit=100
            )
            
            # Calculate average score
            total_score = 0
            score_count = 0
            total_time = 0
            time_count = 0
            
            for task in successful_tasks:
                if task.get("results") and task["results"].get("overall_score_percent"):
                    total_score += task["results"]["overall_score_percent"]
                    score_count += 1
                
                # Calculate analysis time
                if task.get("started_at") and task.get("completed_at"):
                    started = datetime.fromisoformat(task["started_at"].replace('Z', '+00:00'))
                    completed = datetime.fromisoformat(task["completed_at"].replace('Z', '+00:00'))
                    duration = (completed - started).total_seconds()
                    total_time += duration
                    time_count += 1
            
            average_score = total_score / score_count if score_count > 0 else 0.0
            average_analysis_time = total_time / time_count if time_count > 0 else 0.0
            
            return {
                "total_analyses": total_analyses,
                "successful_analyses": successful_analyses,
                "failed_analyses": summary["failed_analyses"],
                "pending_analyses": summary["pending_analyses"],
                "average_score": round(average_score, 2),
                "average_analysis_time": round(average_analysis_time, 2),
                "last_analysis_date": summary["last_analysis_date"]
            }
            
        except Exception as e:
            logger.error("Failed to get dashboard summary", 
                        user_id=user_id, error=str(e))
            return None
    
    async def get_user_analysis_trends(
        self, 
        user_id: str, 
        metric: str = "overall_score",
        days: int = 30
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get analysis trends for user.
        
        Args:
            user_id: User ID
            metric: Metric to trend
            days: Number of days to look back
            
        Returns:
            List of trend data points or None if failed
        """
        try:
            # This would typically use a more complex query
            # For now, return sample trend data
            from datetime import timedelta
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get successful tasks in date range
            tasks = await self.analysis_tasks.get_user_analysis_tasks(
                user_id=user_id,
                status=AnalysisStatus.SUCCESS,
                limit=1000
            )
            
            # Filter tasks by date range
            filtered_tasks = []
            for task in tasks:
                if task.get("completed_at"):
                    completed_date = datetime.fromisoformat(
                        task["completed_at"].replace('Z', '+00:00')
                    )
                    if start_date <= completed_date <= end_date:
                        filtered_tasks.append(task)
            
            # Group by date and calculate averages
            daily_scores = {}
            for task in filtered_tasks:
                if task.get("results") and task["results"].get("overall_score_percent"):
                    date_str = task["completed_at"][:10]  # YYYY-MM-DD
                    score = task["results"]["overall_score_percent"]
                    
                    if date_str not in daily_scores:
                        daily_scores[date_str] = []
                    daily_scores[date_str].append(score)
            
            # Calculate daily averages
            trend_data = []
            for date_str, scores in daily_scores.items():
                avg_score = sum(scores) / len(scores)
                trend_data.append({
                    "date": date_str,
                    "value": round(avg_score, 2)
                })
            
            # Sort by date
            trend_data.sort(key=lambda x: x["date"])
            
            return trend_data
            
        except Exception as e:
            logger.error("Failed to get analysis trends", 
                        user_id=user_id, error=str(e))
            return None
    
    # Batch Operations
    async def batch_create_analysis_tasks(
        self, 
        user_id: str, 
        urls: List[str],
        analysis_type: AnalysisType = AnalysisType.FULL_SEO
    ) -> List[Dict[str, Any]]:
        """
        Create multiple analysis tasks in batch.
        
        Args:
            user_id: User ID
            urls: List of URLs to analyze
            analysis_type: Type of analysis
            
        Returns:
            List of created tasks
        """
        try:
            created_tasks = []
            
            for url in urls:
                task_data = await self.create_analysis_task(
                    user_id=user_id,
                    url=url,
                    analysis_type=analysis_type
                )
                
                if task_data:
                    created_tasks.append(task_data)
            
            logger.info("Batch analysis tasks created", 
                       user_id=user_id, count=len(created_tasks))
            
            return created_tasks
            
        except Exception as e:
            logger.error("Failed to create batch analysis tasks", 
                        user_id=user_id, error=str(e))
            return []
    
    async def batch_update_analysis_tasks(
        self, 
        task_updates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Update multiple analysis tasks in batch.
        
        Args:
            task_updates: List of task updates with task_id and updates
            
        Returns:
            List of updated tasks
        """
        try:
            updated_tasks = []
            
            for update in task_updates:
                task_id = update.get("task_id")
                updates = update.get("updates", {})
                
                if task_id:
                    updated_task = await self.update_analysis_task(task_id, updates)
                    if updated_task:
                        updated_tasks.append(updated_task)
            
            logger.info("Batch analysis tasks updated", count=len(updated_tasks))
            
            return updated_tasks
            
        except Exception as e:
            logger.error("Failed to update batch analysis tasks", error=str(e))
            return []
    
    # Transaction Support
    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """
        Execute multiple database operations in a transaction.
        
        Args:
            operations: List of operations to execute
            
        Returns:
            True if all operations successful
        """
        try:
            # Note: Supabase doesn't have explicit transaction support in Python client
            # This would need to be implemented using RPC calls or direct SQL
            # For now, we'll execute operations sequentially
            
            for operation in operations:
                op_type = operation.get("type")
                op_data = operation.get("data", {})
                
                if op_type == "create_profile":
                    await self.create_user_profile(**op_data)
                elif op_type == "create_analysis_task":
                    await self.create_analysis_task(**op_data)
                elif op_type == "update_analysis_task":
                    await self.update_analysis_task(**op_data)
                # Add more operation types as needed
            
            logger.info("Transaction executed successfully", 
                       operations_count=len(operations))
            
            return True
            
        except Exception as e:
            logger.error("Transaction failed", error=str(e))
            return False
    
    # Connection Management
    async def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information and statistics.
        
        Returns:
            Connection information
        """
        try:
            return {
                "service": "supabase",
                "connected": True,
                "url": self.client.supabase_url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get connection info", error=str(e))
            return {
                "service": "supabase",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


def get_supabase_service(supabase_client: Client) -> SupabaseService:
    """
    Get SupabaseService instance for dependency injection.
    
    Args:
        supabase_client: Supabase client instance
        
    Returns:
        SupabaseService instance
    """
    return SupabaseService(supabase_client)