"""
Database models and helper functions for Core Website Vitals.
Provides utilities for working with Supabase tables and queries.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID
from supabase import Client
from app.models.schemas import AnalysisStatus, AnalysisType, SubscriptionTier
import structlog

logger = structlog.get_logger(__name__)


class SupabaseTableHelper:
    """Helper class for common Supabase table operations."""
    
    def __init__(self, client: Client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.table = client.table(table_name)
    
    async def select_by_id(self, id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Select a single record by ID."""
        try:
            response = self.table.select("*").eq("id", str(id)).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error selecting from {self.table_name} by ID", 
                        id=str(id), error=str(e))
            return None
    
    async def select_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Select all records with limit."""
        try:
            response = self.table.select("*").limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error selecting all from {self.table_name}", error=str(e))
            return []
    
    async def insert(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a new record."""
        try:
            response = self.table.insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error inserting into {self.table_name}", 
                        data=data, error=str(e))
            return None
    
    async def update(self, id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by ID."""
        try:
            response = self.table.update(data).eq("id", str(id)).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating {self.table_name}", 
                        id=str(id), data=data, error=str(e))
            return None
    
    async def delete(self, id: Union[str, UUID]) -> bool:
        """Delete a record by ID."""
        try:
            response = self.table.delete().eq("id", str(id)).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting from {self.table_name}", 
                        id=str(id), error=str(e))
            return False


class ProfilesTable:
    """Helper class for profiles table operations."""
    
    def __init__(self, client: Client):
        self.client = client
        self.table = client.table("profiles")
    
    async def create_profile(self, user_id: str, email: str, full_name: str = None) -> Optional[Dict[str, Any]]:
        """Create a new user profile."""
        try:
            profile_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name or "",
                "subscription_tier": SubscriptionTier.FREE
            }
            
            response = self.table.insert(profile_data).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error("Error creating profile", 
                        user_id=user_id, email=email, error=str(e))
            return None
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID."""
        try:
            response = self.table.select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Error getting profile", user_id=user_id, error=str(e))
            return None
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile."""
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.table.update(updates).eq("id", user_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error("Error updating profile", 
                        user_id=user_id, updates=updates, error=str(e))
            return None
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile."""
        try:
            response = self.table.delete().eq("id", user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error("Error deleting profile", user_id=user_id, error=str(e))
            return False


class AnalysisTasksTable:
    """Helper class for analysis_tasks table operations."""
    
    def __init__(self, client: Client):
        self.client = client
        self.table = client.table("analysis_tasks")
    
    async def create_analysis_task(
        self, 
        user_id: str, 
        url: str, 
        analysis_type: AnalysisType = AnalysisType.FULL_SEO
    ) -> Optional[Dict[str, Any]]:
        """Create a new analysis task."""
        try:
            task_data = {
                "user_id": user_id,
                "url_analyzed": url,
                "status": AnalysisStatus.PENDING,
                "analysis_type": analysis_type
            }
            
            response = self.table.insert(task_data).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error("Error creating analysis task", 
                        user_id=user_id, url=url, error=str(e))
            return None
    
    async def get_analysis_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis task by ID."""
        try:
            response = self.table.select("*").eq("id", task_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Error getting analysis task", task_id=task_id, error=str(e))
            return None
    
    async def get_user_analysis_tasks(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        status: Optional[AnalysisStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get user's analysis tasks with pagination."""
        try:
            query = self.table.select("*").eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status)
            
            query = query.order("submitted_at", desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error("Error getting user analysis tasks", 
                        user_id=user_id, error=str(e))
            return []
    
    async def update_analysis_task(
        self, 
        task_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update analysis task."""
        try:
            response = self.table.update(updates).eq("id", task_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error("Error updating analysis task", 
                        task_id=task_id, updates=updates, error=str(e))
            return None
    
    async def set_task_status(
        self, 
        task_id: str, 
        status: AnalysisStatus,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Set analysis task status."""
        try:
            updates = {"status": status}
            
            if status == AnalysisStatus.IN_PROGRESS:
                updates["started_at"] = datetime.utcnow().isoformat()
            elif status in [AnalysisStatus.SUCCESS, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
                updates["completed_at"] = datetime.utcnow().isoformat()
            
            if error_message:
                updates["error_message"] = error_message
            
            return await self.update_analysis_task(task_id, updates)
            
        except Exception as e:
            logger.error("Error setting task status", 
                        task_id=task_id, status=status, error=str(e))
            return None
    
    async def set_task_results(
        self, 
        task_id: str, 
        results: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Set analysis task results."""
        try:
            updates = {
                "results": results,
                "status": AnalysisStatus.SUCCESS,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            return await self.update_analysis_task(task_id, updates)
            
        except Exception as e:
            logger.error("Error setting task results", 
                        task_id=task_id, error=str(e))
            return None
    
    async def get_user_analysis_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's analysis summary statistics."""
        try:
            # This would typically use a view or aggregation query
            # For now, we'll implement basic counting
            response = self.table.select("status, submitted_at, completed_at, started_at").eq("user_id", user_id).execute()
            
            if not response.data:
                return {
                    "total_analyses": 0,
                    "successful_analyses": 0,
                    "failed_analyses": 0,
                    "pending_analyses": 0,
                    "last_analysis_date": None
                }
            
            tasks = response.data
            
            summary = {
                "total_analyses": len(tasks),
                "successful_analyses": sum(1 for t in tasks if t["status"] == AnalysisStatus.SUCCESS),
                "failed_analyses": sum(1 for t in tasks if t["status"] == AnalysisStatus.FAILED),
                "pending_analyses": sum(1 for t in tasks if t["status"] == AnalysisStatus.PENDING),
                "last_analysis_date": max(
                    (t["submitted_at"] for t in tasks if t["submitted_at"]),
                    default=None
                )
            }
            
            return summary
            
        except Exception as e:
            logger.error("Error getting user analysis summary", 
                        user_id=user_id, error=str(e))
            return None
    
    async def delete_analysis_task(self, task_id: str) -> bool:
        """Delete analysis task."""
        try:
            response = self.table.delete().eq("id", task_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error("Error deleting analysis task", task_id=task_id, error=str(e))
            return False


class DatabaseManager:
    """Main database manager class."""
    
    def __init__(self, client: Client):
        self.client = client
        self.profiles = ProfilesTable(client)
        self.analysis_tasks = AnalysisTasksTable(client)
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            # Simple query to test connection
            response = self.client.table("profiles").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def get_table_helper(self, table_name: str) -> SupabaseTableHelper:
        """Get a generic table helper."""
        return SupabaseTableHelper(self.client, table_name)


# Query builders for complex operations
class QueryBuilder:
    """Builder class for complex database queries."""
    
    def __init__(self, client: Client):
        self.client = client
    
    def build_analysis_trends_query(
        self, 
        user_id: str, 
        days: int = 30, 
        metric: str = "overall_score"
    ) -> str:
        """Build query for analysis trends."""
        # This would return a complex query for trend analysis
        # For now, return a placeholder
        return f"""
        SELECT 
            DATE_TRUNC('day', submitted_at) as date,
            AVG(CAST(results->>'{metric}' AS FLOAT)) as avg_score
        FROM analysis_tasks 
        WHERE user_id = '{user_id}' 
        AND submitted_at >= NOW() - INTERVAL '{days} days'
        AND status = 'SUCCESS'
        AND results IS NOT NULL
        GROUP BY DATE_TRUNC('day', submitted_at)
        ORDER BY date ASC
        """
    
    def build_dashboard_metrics_query(self, user_id: str) -> str:
        """Build query for dashboard metrics."""
        return f"""
        SELECT 
            AVG(CAST(results->'seo_attributes'->'ScoringModule'->>'on_page_score_percent' AS FLOAT)) as avg_on_page,
            AVG(CAST(results->'seo_attributes'->'ScoringModule'->>'technical_score_percent' AS FLOAT)) as avg_technical,
            AVG(CAST(results->'seo_attributes'->'ScoringModule'->>'content_score_percent' AS FLOAT)) as avg_content,
            AVG(CAST(results->'seo_attributes'->'ScoringModule'->>'overall_seo_score_percent' AS FLOAT)) as avg_overall
        FROM analysis_tasks 
        WHERE user_id = '{user_id}' 
        AND status = 'SUCCESS'
        AND results IS NOT NULL
        """


# Export main classes
__all__ = [
    "DatabaseManager",
    "ProfilesTable", 
    "AnalysisTasksTable",
    "SupabaseTableHelper",
    "QueryBuilder"
]