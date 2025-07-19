# Email Setup Guide for Core Website Vitals

This guide explains how to set up email functionality for Core Website Vitals using Resend and Supabase.

## Overview

Core Website Vitals uses two email systems:
1. **Supabase Auth Emails**: For authentication-related emails (verification, password reset)
2. **Resend**: For transactional emails (welcome emails, analysis notifications)

## Supabase Email Configuration

### Option 1: Using Supabase's Built-in Email Service (Development)

By default, Supabase provides a built-in email service for development. Emails are captured in Inbucket (local email testing server).

Access Inbucket at: http://localhost:54324

### Option 2: Using Resend with Supabase (Production)

1. **Get your Resend API Key**:
   - Sign up at [Resend.com](https://resend.com)
   - Create an API key from the dashboard
   - Add your domain and verify it

2. **Configure Supabase to use Resend**:

   Update your `supabase/config.toml`:

   ```toml
   [auth.email]
   enable_signup = true
   double_confirm_changes = true
   enable_confirmations = true  # Enable email confirmation
   
   [auth.email.smtp]
   enabled = true
   host = "smtp.resend.com"
   port = 465
   user = "resend"
   pass = "env(RESEND_API_KEY)"
   admin_email = "admin@corewebsitevitals.com"
   sender_name = "Core Website Vitals"
   ```

3. **Set Environment Variables**:

   Create a `.env` file in your supabase directory:
   ```bash
   RESEND_API_KEY=re_your_resend_api_key_here
   ```

4. **Restart Supabase**:
   ```bash
   supabase stop
   supabase start
   ```

### Option 3: Using SendGrid with Supabase

If you prefer SendGrid:

```toml
[auth.email.smtp]
enabled = true
host = "smtp.sendgrid.net"
port = 587
user = "apikey"
pass = "env(SENDGRID_API_KEY)"
admin_email = "admin@corewebsitevitals.com"
sender_name = "Core Website Vitals"
```

## Backend Email Configuration

The backend uses Resend for sending transactional emails (non-auth emails).

1. **Set Environment Variables**:

   Update your backend `.env` file:
   ```env
   # Email Configuration
   ENABLE_EMAIL_NOTIFICATIONS=True
   RESEND_API_KEY=re_your_resend_api_key_here
   EMAIL_FROM_ADDRESS=noreply@corewebsitevitals.com
   EMAIL_FROM_NAME=Core Website Vitals
   ```

2. **Verify Domain in Resend**:
   - Log in to Resend dashboard
   - Add your domain (corewebsitevitals.com)
   - Add the DNS records as instructed
   - Wait for verification

## Email Templates

### Supabase Auth Email Templates

You can customize Supabase auth emails by creating template files:

1. Create template directory:
   ```bash
   mkdir -p supabase/templates
   ```

2. Create custom templates:

   **Confirmation Email** (`supabase/templates/confirmation.html`):
   ```html
   <h2>Confirm your email</h2>
   <p>Follow this link to confirm your email:</p>
   <p><a href="{{ .ConfirmationURL }}">Confirm your email address</a></p>
   ```

   **Reset Password Email** (`supabase/templates/reset.html`):
   ```html
   <h2>Reset your password</h2>
   <p>Follow this link to reset your password:</p>
   <p><a href="{{ .ConfirmationURL }}">Reset Password</a></p>
   ```

3. Update `supabase/config.toml`:
   ```toml
   [auth.email.template.confirmation]
   subject = "Confirm your Core Website Vitals account"
   content_path = "./supabase/templates/confirmation.html"
   
   [auth.email.template.reset]
   subject = "Reset your Core Website Vitals password"
   content_path = "./supabase/templates/reset.html"
   ```

### Backend Email Templates

Backend email templates are defined in `/backend/app/services/email_service.py`. Currently includes:

- Welcome email
- Email verification
- Password reset
- Analysis complete notification

## Testing Emails

### Local Development

1. **Check Inbucket** (for Supabase auth emails):
   - Visit http://localhost:54324
   - All auth emails will appear here

2. **Check Backend Logs** (for transactional emails):
   - When `ENABLE_EMAIL_NOTIFICATIONS=False`, emails are logged instead of sent
   - Check backend logs to see what would have been sent

3. **Use Resend Test Mode**:
   - Use a test API key from Resend
   - Emails won't be sent but will appear in Resend dashboard

### Production Testing

1. **Use Resend Dashboard**:
   - Monitor sent emails
   - Check delivery status
   - View email analytics

2. **Test with Real Emails**:
   - Create test accounts with real email addresses
   - Verify emails are delivered correctly

## Troubleshooting

### Emails Not Sending

1. **Check API Keys**:
   - Verify RESEND_API_KEY is set correctly
   - Ensure the key has proper permissions

2. **Check Domain Verification**:
   - Ensure your domain is verified in Resend
   - DNS records are properly configured

3. **Check Logs**:
   ```bash
   # Backend logs
   docker-compose logs backend
   
   # Supabase logs
   supabase status
   ```

### Emails Going to Spam

1. **Set up SPF, DKIM, and DMARC**:
   - Follow Resend's domain verification guide
   - Add all required DNS records

2. **Use a Dedicated Domain**:
   - Use a subdomain like `mail.corewebsitevitals.com`
   - Avoid using free email providers

3. **Email Content**:
   - Avoid spam trigger words
   - Include unsubscribe links
   - Use proper HTML structure

## Production Checklist

- [ ] Resend API key configured
- [ ] Domain verified in Resend
- [ ] SPF, DKIM, DMARC records added
- [ ] Email templates customized
- [ ] Test emails sent successfully
- [ ] Email monitoring set up
- [ ] Backup SMTP provider configured (optional)

## Support

For issues with:
- **Resend**: Contact support@resend.com
- **Supabase**: Visit https://supabase.com/docs/guides/auth/auth-email
- **Core Website Vitals**: Check backend logs and Supabase logs