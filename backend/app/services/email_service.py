"""
Email service for sending transactional emails using Resend.
"""

import logging
from typing import Optional, List, Dict, Any
import resend
from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend."""
    
    def __init__(self):
        """Initialize the email service with Resend API key."""
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            self.enabled = settings.ENABLE_EMAIL_NOTIFICATIONS
        else:
            self.enabled = False
            logger.warning("Resend API key not configured. Email sending disabled.")
    
    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email to new user."""
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send welcome email to {email}")
            return True
        
        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                "to": [email],
                "subject": "Welcome to Core Website Vitals!",
                "html": self._get_welcome_email_html(name),
                "text": self._get_welcome_email_text(name),
            }
            
            result = resend.Emails.send(params)
            logger.info(f"Welcome email sent to {email}. ID: {result.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            return False
    
    async def send_verification_email(self, email: str, name: str, verification_url: str) -> bool:
        """Send email verification link."""
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send verification email to {email}")
            return True
        
        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                "to": [email],
                "subject": "Verify your Core Website Vitals account",
                "html": self._get_verification_email_html(name, verification_url),
                "text": self._get_verification_email_text(name, verification_url),
            }
            
            result = resend.Emails.send(params)
            logger.info(f"Verification email sent to {email}. ID: {result.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False
    
    async def send_password_reset_email(self, email: str, name: str, reset_url: str) -> bool:
        """Send password reset email."""
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send password reset email to {email}")
            return True
        
        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                "to": [email],
                "subject": "Reset your Core Website Vitals password",
                "html": self._get_password_reset_email_html(name, reset_url),
                "text": self._get_password_reset_email_text(name, reset_url),
            }
            
            result = resend.Emails.send(params)
            logger.info(f"Password reset email sent to {email}. ID: {result.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False
    
    async def send_analysis_complete_email(
        self, 
        email: str, 
        name: str, 
        url_analyzed: str, 
        analysis_url: str,
        score: int
    ) -> bool:
        """Send email notification when analysis is complete."""
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send analysis complete email to {email}")
            return True
        
        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>",
                "to": [email],
                "subject": f"SEO Analysis Complete for {url_analyzed}",
                "html": self._get_analysis_complete_email_html(name, url_analyzed, analysis_url, score),
                "text": self._get_analysis_complete_email_text(name, url_analyzed, analysis_url, score),
            }
            
            result = resend.Emails.send(params)
            logger.info(f"Analysis complete email sent to {email}. ID: {result.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send analysis complete email to {email}: {str(e)}")
            return False
    
    # Email templates
    def _get_welcome_email_html(self, name: str) -> str:
        """Get HTML template for welcome email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Core Website Vitals</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #1a73e8;">Welcome to Core Website Vitals!</h1>
                <p>Hi {name},</p>
                <p>Thank you for signing up! We're excited to have you on board.</p>
                <p>With Core Website Vitals, you can:</p>
                <ul>
                    <li>Get comprehensive SEO analysis for your websites</li>
                    <li>Monitor Core Web Vitals and performance metrics</li>
                    <li>Track your progress over time</li>
                    <li>Receive actionable recommendations</li>
                </ul>
                <p>
                    <a href="{settings.FRONTEND_URL}/dashboard" 
                       style="display: inline-block; padding: 10px 20px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px;">
                        Go to Dashboard
                    </a>
                </p>
                <p>If you have any questions, feel free to reach out to our support team.</p>
                <p>Best regards,<br>The Core Website Vitals Team</p>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_email_text(self, name: str) -> str:
        """Get text template for welcome email."""
        return f"""
Welcome to Core Website Vitals!

Hi {name},

Thank you for signing up! We're excited to have you on board.

With Core Website Vitals, you can:
- Get comprehensive SEO analysis for your websites
- Monitor Core Web Vitals and performance metrics
- Track your progress over time
- Receive actionable recommendations

Go to Dashboard: {settings.FRONTEND_URL}/dashboard

If you have any questions, feel free to reach out to our support team.

Best regards,
The Core Website Vitals Team
        """
    
    def _get_verification_email_html(self, name: str, verification_url: str) -> str:
        """Get HTML template for verification email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify your email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #1a73e8;">Verify your email address</h1>
                <p>Hi {name},</p>
                <p>Please click the button below to verify your email address and activate your account:</p>
                <p style="margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="display: inline-block; padding: 12px 30px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Verify Email Address
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{verification_url}</p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't create an account, you can safely ignore this email.</p>
                <p>Best regards,<br>The Core Website Vitals Team</p>
            </div>
        </body>
        </html>
        """
    
    def _get_verification_email_text(self, name: str, verification_url: str) -> str:
        """Get text template for verification email."""
        return f"""
Verify your email address

Hi {name},

Please click the link below to verify your email address and activate your account:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

Best regards,
The Core Website Vitals Team
        """
    
    def _get_password_reset_email_html(self, name: str, reset_url: str) -> str:
        """Get HTML template for password reset email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset your password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #1a73e8;">Reset your password</h1>
                <p>Hi {name},</p>
                <p>We received a request to reset your password. Click the button below to set a new password:</p>
                <p style="margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="display: inline-block; padding: 12px 30px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, you can safely ignore this email.</p>
                <p>Best regards,<br>The Core Website Vitals Team</p>
            </div>
        </body>
        </html>
        """
    
    def _get_password_reset_email_text(self, name: str, reset_url: str) -> str:
        """Get text template for password reset email."""
        return f"""
Reset your password

Hi {name},

We received a request to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
The Core Website Vitals Team
        """
    
    def _get_analysis_complete_email_html(self, name: str, url_analyzed: str, analysis_url: str, score: int) -> str:
        """Get HTML template for analysis complete email."""
        score_color = "#4ade80" if score >= 80 else "#fbbf24" if score >= 60 else "#ef4444"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>SEO Analysis Complete</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #1a73e8;">Your SEO Analysis is Ready!</h1>
                <p>Hi {name},</p>
                <p>The SEO analysis for <strong>{url_analyzed}</strong> has been completed.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <p style="margin: 0; color: #666;">Overall SEO Score</p>
                    <p style="font-size: 48px; font-weight: bold; color: {score_color}; margin: 10px 0;">{score}%</p>
                </div>
                <p style="margin: 30px 0;">
                    <a href="{analysis_url}" 
                       style="display: inline-block; padding: 12px 30px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View Full Report
                    </a>
                </p>
                <p>Your report includes:</p>
                <ul>
                    <li>Core Web Vitals assessment</li>
                    <li>Technical SEO audit</li>
                    <li>Content optimization suggestions</li>
                    <li>Mobile performance analysis</li>
                    <li>Actionable recommendations</li>
                </ul>
                <p>Best regards,<br>The Core Website Vitals Team</p>
            </div>
        </body>
        </html>
        """
    
    def _get_analysis_complete_email_text(self, name: str, url_analyzed: str, analysis_url: str, score: int) -> str:
        """Get text template for analysis complete email."""
        return f"""
Your SEO Analysis is Ready!

Hi {name},

The SEO analysis for {url_analyzed} has been completed.

Overall SEO Score: {score}%

View Full Report: {analysis_url}

Your report includes:
- Core Web Vitals assessment
- Technical SEO audit
- Content optimization suggestions
- Mobile performance analysis
- Actionable recommendations

Best regards,
The Core Website Vitals Team
        """


# Create global email service instance
email_service = EmailService()