"""
SEO Analysis endpoints for Core Website Vitals API.
Handles analysis submission, status tracking, and result retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.core.security import get_current_user_id
from app.core.supabase import get_cached_supabase_client
from app.services.supabase_service import get_supabase_service
from app.worker.tasks import perform_seo_analysis, cancel_analysis_task
from app.models.schemas import (
    AnalysisTaskCreate,
    AnalysisTaskResponse,
    AnalysisTaskListResponse,
    AnalysisTaskUpdate,
    AnalysisStatus,
    AnalysisType
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=AnalysisTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(
    analysis_data: AnalysisTaskCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Submit a new SEO analysis task.
    
    Args:
        analysis_data: Analysis task creation data
        current_user_id: Current authenticated user ID
        
    Returns:
        Created analysis task with pending status
    """
    try:
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Create analysis task in database
        task_data = await db_service.create_analysis_task(
            user_id=current_user_id,
            url=str(analysis_data.url),
            analysis_type=analysis_data.analysis_type
        )
        
        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create analysis task"
            )
        
        # Submit Celery task
        celery_task = perform_seo_analysis.delay(
            analysis_task_id=task_data["id"],
            url=str(analysis_data.url),
            analysis_type=analysis_data.analysis_type.value,
            user_id=current_user_id
        )
        
        # Update task with Celery task ID
        await db_service.update_analysis_task(
            task_data["id"],
            {"celery_task_id": celery_task.id}
        )
        
        logger.info("Analysis task submitted successfully", 
                   task_id=task_data["id"], 
                   url=str(analysis_data.url),
                   user_id=current_user_id)
        
        return AnalysisTaskResponse(
            id=task_data["id"],
            user_id=task_data["user_id"],
            url_analyzed=task_data["url_analyzed"],
            status=AnalysisStatus(task_data["status"]),
            analysis_type=AnalysisType(task_data["analysis_type"]),
            celery_task_id=celery_task.id,
            submitted_at=datetime.fromisoformat(task_data["submitted_at"]),
            started_at=None,
            completed_at=None,
            results=None,
            error_message=None
        )
        
    except Exception as e:
        logger.error("Analysis submission failed", 
                    url=str(analysis_data.url), 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit analysis"
        )


@router.get("/", response_model=AnalysisTaskListResponse)
async def list_analyses(
    current_user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    analysis_type: Optional[str] = Query(None, description="Filter by analysis type")
):
    """
    List user's analysis tasks with pagination and filtering.
    
    Args:
        current_user_id: Current authenticated user ID
        page: Page number (1-based)
        page_size: Number of items per page
        status_filter: Optional status filter
        analysis_type: Optional analysis type filter
        
    Returns:
        Paginated list of analysis tasks
    """
    try:
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = AnalysisStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Get user's analysis tasks
        tasks = await db_service.get_user_analysis_tasks(
            user_id=current_user_id,
            limit=page_size,
            offset=offset,
            status=status_enum
        )
        
        # Get total count for pagination
        # This would be a separate query in a real implementation
        total_tasks = await db_service.get_user_analysis_tasks(
            user_id=current_user_id,
            limit=1000,  # Large number to get total count
            offset=0,
            status=status_enum
        )
        total = len(total_tasks)
        
        # Convert to response objects
        task_responses = []
        for task in tasks:
            task_responses.append(AnalysisTaskResponse(
                id=task["id"],
                user_id=task["user_id"],
                url_analyzed=task["url_analyzed"],
                status=AnalysisStatus(task["status"]),
                analysis_type=AnalysisType(task["analysis_type"]),
                celery_task_id=task.get("celery_task_id"),
                submitted_at=datetime.fromisoformat(task["submitted_at"]),
                started_at=datetime.fromisoformat(task["started_at"]) if task.get("started_at") else None,
                completed_at=datetime.fromisoformat(task["completed_at"]) if task.get("completed_at") else None,
                results=task.get("results"),
                error_message=task.get("error_message")
            ))
        
        # Calculate pagination info
        pages = (total + page_size - 1) // page_size
        
        return AnalysisTaskListResponse(
            items=task_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )
        
    except Exception as e:
        logger.error("Analysis listing failed", 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list analyses"
        )


@router.get("/{analysis_id}", response_model=AnalysisTaskResponse)
async def get_analysis(
    analysis_id: UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get detailed analysis results by ID.
    
    Args:
        analysis_id: Analysis task ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Analysis task with results
    """
    try:
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Get analysis task
        task = await db_service.get_analysis_task(str(analysis_id))
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis task not found"
            )
        
        # Check if user owns this task
        if task["user_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return AnalysisTaskResponse(
            id=task["id"],
            user_id=task["user_id"],
            url_analyzed=task["url_analyzed"],
            status=AnalysisStatus(task["status"]),
            analysis_type=AnalysisType(task["analysis_type"]),
            celery_task_id=task.get("celery_task_id"),
            submitted_at=datetime.fromisoformat(task["submitted_at"]),
            started_at=datetime.fromisoformat(task["started_at"]) if task.get("started_at") else None,
            completed_at=datetime.fromisoformat(task["completed_at"]) if task.get("completed_at") else None,
            results=task.get("results"),
            error_message=task.get("error_message")
        )
        
    except Exception as e:
        logger.error("Get analysis failed", 
                    analysis_id=str(analysis_id), 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis"
        )


@router.put("/{analysis_id}", response_model=AnalysisTaskResponse)
async def update_analysis(
    analysis_id: UUID,
    analysis_update: AnalysisTaskUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update analysis task (e.g., cancel running analysis).
    
    Args:
        analysis_id: Analysis task ID
        analysis_update: Update data
        current_user_id: Current authenticated user ID
        
    Returns:
        Updated analysis task
    """
    try:
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Get analysis task
        task = await db_service.get_analysis_task(str(analysis_id))
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis task not found"
            )
        
        # Check if user owns this task
        if task["user_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Handle status update (mainly for cancellation)
        if analysis_update.status:
            if analysis_update.status == AnalysisStatus.CANCELLED:
                # Cancel the Celery task if it exists
                if task.get("celery_task_id"):
                    cancel_analysis_task.delay(
                        analysis_task_id=str(analysis_id),
                        user_id=current_user_id
                    )
                
                # Update task status in database
                updated_task = await db_service.set_analysis_task_status(
                    str(analysis_id),
                    AnalysisStatus.CANCELLED
                )
                
                if not updated_task:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to update analysis status"
                    )
                
                logger.info("Analysis task cancelled", 
                           analysis_id=str(analysis_id), 
                           user_id=current_user_id)
                
                return AnalysisTaskResponse(
                    id=updated_task["id"],
                    user_id=updated_task["user_id"],
                    url_analyzed=updated_task["url_analyzed"],
                    status=AnalysisStatus(updated_task["status"]),
                    analysis_type=AnalysisType(updated_task["analysis_type"]),
                    celery_task_id=updated_task.get("celery_task_id"),
                    submitted_at=datetime.fromisoformat(updated_task["submitted_at"]),
                    started_at=datetime.fromisoformat(updated_task["started_at"]) if updated_task.get("started_at") else None,
                    completed_at=datetime.fromisoformat(updated_task["completed_at"]) if updated_task.get("completed_at") else None,
                    results=updated_task.get("results"),
                    error_message=updated_task.get("error_message")
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only cancellation is supported for status updates"
                )
        
        # If no updates provided, return current task
        return AnalysisTaskResponse(
            id=task["id"],
            user_id=task["user_id"],
            url_analyzed=task["url_analyzed"],
            status=AnalysisStatus(task["status"]),
            analysis_type=AnalysisType(task["analysis_type"]),
            celery_task_id=task.get("celery_task_id"),
            submitted_at=datetime.fromisoformat(task["submitted_at"]),
            started_at=datetime.fromisoformat(task["started_at"]) if task.get("started_at") else None,
            completed_at=datetime.fromisoformat(task["completed_at"]) if task.get("completed_at") else None,
            results=task.get("results"),
            error_message=task.get("error_message")
        )
        
    except Exception as e:
        logger.error("Analysis update failed", 
                    analysis_id=str(analysis_id), 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update analysis"
        )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete an analysis task.
    
    Args:
        analysis_id: Analysis task ID
        current_user_id: Current authenticated user ID
    """
    try:
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Get analysis task
        task = await db_service.get_analysis_task(str(analysis_id))
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis task not found"
            )
        
        # Check if user owns this task
        if task["user_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Cancel the Celery task if it's running
        if task.get("celery_task_id") and task["status"] in [AnalysisStatus.PENDING, AnalysisStatus.IN_PROGRESS]:
            cancel_analysis_task.delay(
                analysis_task_id=str(analysis_id),
                user_id=current_user_id
            )
        
        # Delete the analysis task
        deleted = await db_service.delete_analysis_task(str(analysis_id))
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete analysis task"
            )
        
        logger.info("Analysis task deleted", 
                   analysis_id=str(analysis_id), 
                   user_id=current_user_id)
        
    except Exception as e:
        logger.error("Analysis deletion failed", 
                    analysis_id=str(analysis_id), 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis"
        )


@router.get("/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get analysis task status and progress.
    
    Args:
        analysis_id: Analysis task ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Analysis task status information
    """
    try:
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Get analysis task
        task = await db_service.get_analysis_task(str(analysis_id))
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis task not found"
            )
        
        # Check if user owns this task
        if task["user_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Calculate progress and estimated completion
        progress_percentage = 0
        estimated_completion = None
        
        if task["status"] == AnalysisStatus.PENDING:
            progress_percentage = 0
        elif task["status"] == AnalysisStatus.IN_PROGRESS:
            progress_percentage = 50  # Rough estimate
            if task.get("started_at"):
                started_at = datetime.fromisoformat(task["started_at"])
                elapsed = datetime.utcnow() - started_at
                # Rough estimate: full analysis takes 2-5 minutes
                if elapsed.total_seconds() > 300:  # 5 minutes
                    progress_percentage = 90
                elif elapsed.total_seconds() > 120:  # 2 minutes
                    progress_percentage = 70
        elif task["status"] == AnalysisStatus.SUCCESS:
            progress_percentage = 100
        elif task["status"] == AnalysisStatus.FAILED:
            progress_percentage = 0
        elif task["status"] == AnalysisStatus.CANCELLED:
            progress_percentage = 0
        
        return {
            "analysis_id": str(analysis_id),
            "status": task["status"],
            "progress_percentage": progress_percentage,
            "submitted_at": task["submitted_at"],
            "started_at": task.get("started_at"),
            "completed_at": task.get("completed_at"),
            "estimated_completion": estimated_completion,
            "error_message": task.get("error_message"),
            "celery_task_id": task.get("celery_task_id")
        }
        
    except Exception as e:
        logger.error("Get analysis status failed", 
                    analysis_id=str(analysis_id), 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis status"
        )


@router.post("/{analysis_id}/retry", response_model=AnalysisTaskResponse)
async def retry_analysis(
    analysis_id: UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Retry a failed analysis task.
    
    Args:
        analysis_id: Analysis task ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Restarted analysis task
    """
    try:
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Get analysis task
        task = await db_service.get_analysis_task(str(analysis_id))
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis task not found"
            )
        
        # Check if user owns this task
        if task["user_id"] != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if task can be retried
        if task["status"] not in [AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only failed or cancelled tasks can be retried"
            )
        
        # Reset task status to pending
        updated_task = await db_service.set_analysis_task_status(
            str(analysis_id),
            AnalysisStatus.PENDING
        )
        
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset analysis task status"
            )
        
        # Submit new Celery task
        celery_task = perform_seo_analysis.delay(
            analysis_task_id=str(analysis_id),
            url=task["url_analyzed"],
            analysis_type=task["analysis_type"],
            user_id=current_user_id
        )
        
        # Update task with new Celery task ID
        final_task = await db_service.update_analysis_task(
            str(analysis_id),
            {
                "celery_task_id": celery_task.id,
                "error_message": None,
                "results": None
            }
        )
        
        logger.info("Analysis task retried", 
                   analysis_id=str(analysis_id), 
                   user_id=current_user_id)
        
        return AnalysisTaskResponse(
            id=final_task["id"],
            user_id=final_task["user_id"],
            url_analyzed=final_task["url_analyzed"],
            status=AnalysisStatus(final_task["status"]),
            analysis_type=AnalysisType(final_task["analysis_type"]),
            celery_task_id=celery_task.id,
            submitted_at=datetime.fromisoformat(final_task["submitted_at"]),
            started_at=None,
            completed_at=None,
            results=None,
            error_message=None
        )
        
    except Exception as e:
        logger.error("Analysis retry failed", 
                    analysis_id=str(analysis_id), 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry analysis"
        )


@router.post("/batch", response_model=List[AnalysisTaskResponse])
async def submit_batch_analysis(
    urls: List[str],
    analysis_type: AnalysisType = AnalysisType.FULL_SEO,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Submit multiple URLs for analysis.
    
    Args:
        urls: List of URLs to analyze
        analysis_type: Type of analysis to perform
        current_user_id: Current authenticated user ID
        
    Returns:
        List of created analysis tasks
    """
    try:
        if len(urls) > 10:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 10 URLs"
            )
        
        # Get database service
        supabase_client = get_cached_supabase_client()
        db_service = get_supabase_service(supabase_client)
        
        # Create analysis tasks for each URL
        created_tasks = []
        analysis_task_ids = []
        
        for url in urls:
            task_data = await db_service.create_analysis_task(
                user_id=current_user_id,
                url=url,
                analysis_type=analysis_type
            )
            
            if task_data:
                created_tasks.append(task_data)
                analysis_task_ids.append(task_data["id"])
        
        # Submit batch Celery task
        from app.worker.tasks import batch_seo_analysis
        celery_task = batch_seo_analysis.delay(
            analysis_task_ids=analysis_task_ids,
            urls=urls,
            analysis_type=analysis_type.value,
            user_id=current_user_id
        )
        
        # Update tasks with Celery task ID
        for task_data in created_tasks:
            await db_service.update_analysis_task(
                task_data["id"],
                {"celery_task_id": celery_task.id}
            )
        
        logger.info("Batch analysis submitted", 
                   url_count=len(urls), 
                   user_id=current_user_id)
        
        # Return created tasks
        response_tasks = []
        for task_data in created_tasks:
            response_tasks.append(AnalysisTaskResponse(
                id=task_data["id"],
                user_id=task_data["user_id"],
                url_analyzed=task_data["url_analyzed"],
                status=AnalysisStatus(task_data["status"]),
                analysis_type=AnalysisType(task_data["analysis_type"]),
                celery_task_id=celery_task.id,
                submitted_at=datetime.fromisoformat(task_data["submitted_at"]),
                started_at=None,
                completed_at=None,
                results=None,
                error_message=None
            ))
        
        return response_tasks
        
    except Exception as e:
        logger.error("Batch analysis submission failed", 
                    url_count=len(urls), 
                    user_id=current_user_id, 
                    error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit batch analysis"
        )