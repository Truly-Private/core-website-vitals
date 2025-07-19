export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          email: string
          full_name: string | null
          avatar_url: string | null
          subscription_tier: string
          created_at: string
          updated_at: string | null
        }
        Insert: {
          id: string
          email: string
          full_name?: string | null
          avatar_url?: string | null
          subscription_tier?: string
          created_at?: string
          updated_at?: string | null
        }
        Update: {
          id?: string
          email?: string
          full_name?: string | null
          avatar_url?: string | null
          subscription_tier?: string
          created_at?: string
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "profiles_id_fkey"
            columns: ["id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      analysis_tasks: {
        Row: {
          id: string
          user_id: string
          url_analyzed: string
          status: string
          celery_task_id: string | null
          submitted_at: string
          started_at: string | null
          completed_at: string | null
          results: Json | null
          error_message: string | null
          analysis_type: string
        }
        Insert: {
          id?: string
          user_id: string
          url_analyzed: string
          status?: string
          celery_task_id?: string | null
          submitted_at?: string
          started_at?: string | null
          completed_at?: string | null
          results?: Json | null
          error_message?: string | null
          analysis_type?: string
        }
        Update: {
          id?: string
          user_id?: string
          url_analyzed?: string
          status?: string
          celery_task_id?: string | null
          submitted_at?: string
          started_at?: string | null
          completed_at?: string | null
          results?: Json | null
          error_message?: string | null
          analysis_type?: string
        }
        Relationships: [
          {
            foreignKeyName: "analysis_tasks_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      user_settings: {
        Row: {
          id: string
          user_id: string
          theme: string
          language: string
          timezone: string
          notifications: Json
          privacy: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          theme?: string
          language?: string
          timezone?: string
          notifications?: Json
          privacy?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          theme?: string
          language?: string
          timezone?: string
          notifications?: Json
          privacy?: Json
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "user_settings_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      subscriptions: {
        Row: {
          id: string
          user_id: string
          tier: string
          status: string
          current_period_start: string
          current_period_end: string
          cancel_at_period_end: boolean
          stripe_subscription_id: string | null
          stripe_customer_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          tier: string
          status: string
          current_period_start: string
          current_period_end: string
          cancel_at_period_end?: boolean
          stripe_subscription_id?: string | null
          stripe_customer_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          tier?: string
          status?: string
          current_period_start?: string
          current_period_end?: string
          cancel_at_period_end?: boolean
          stripe_subscription_id?: string | null
          stripe_customer_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "subscriptions_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      usage_stats: {
        Row: {
          id: string
          user_id: string
          month: string
          analyses_count: number
          storage_used_mb: number
          api_calls_count: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          month: string
          analyses_count?: number
          storage_used_mb?: number
          api_calls_count?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          month?: string
          analyses_count?: number
          storage_used_mb?: number
          api_calls_count?: number
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "usage_stats_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      scheduled_analyses: {
        Row: {
          id: string
          user_id: string
          url: string
          analysis_type: string
          frequency: string
          next_run: string
          is_active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          url: string
          analysis_type: string
          frequency: string
          next_run: string
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          url?: string
          analysis_type?: string
          frequency?: string
          next_run?: string
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "scheduled_analyses_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      api_keys: {
        Row: {
          id: string
          user_id: string
          name: string
          key_hash: string
          permissions: Json
          last_used: string | null
          is_active: boolean
          expires_at: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          key_hash: string
          permissions?: Json
          last_used?: string | null
          is_active?: boolean
          expires_at?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          key_hash?: string
          permissions?: Json
          last_used?: string | null
          is_active?: boolean
          expires_at?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "api_keys_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
      webhooks: {
        Row: {
          id: string
          user_id: string
          url: string
          events: Json
          secret: string
          is_active: boolean
          last_triggered: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          url: string
          events: Json
          secret: string
          is_active?: boolean
          last_triggered?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          url?: string
          events?: Json
          secret?: string
          is_active?: boolean
          last_triggered?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "webhooks_user_id_fkey"
            columns: ["user_id"]
            referencedRelation: "users"
            referencedColumns: ["id"]
          }
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      subscription_tier: 'free' | 'pro' | 'business' | 'enterprise'
      subscription_status: 'active' | 'canceled' | 'past_due' | 'unpaid'
      analysis_status: 'PENDING' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILED' | 'CANCELLED'
      analysis_type: 'full_seo' | 'technical_seo' | 'content_analysis' | 'performance_audit'
      frequency: 'daily' | 'weekly' | 'monthly'
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

// Type helpers
export type Tables<T extends keyof Database['public']['Tables']> = Database['public']['Tables'][T]['Row']
export type Inserts<T extends keyof Database['public']['Tables']> = Database['public']['Tables'][T]['Insert']
export type Updates<T extends keyof Database['public']['Tables']> = Database['public']['Tables'][T]['Update']
export type Enums<T extends keyof Database['public']['Enums']> = Database['public']['Enums'][T]

// Specific table types
export type Profile = Tables<'profiles'>
export type AnalysisTask = Tables<'analysis_tasks'>
export type UserSettings = Tables<'user_settings'>
export type Subscription = Tables<'subscriptions'>
export type UsageStats = Tables<'usage_stats'>
export type ScheduledAnalysis = Tables<'scheduled_analyses'>
export type ApiKey = Tables<'api_keys'>
export type Webhook = Tables<'webhooks'>

// Insert types
export type ProfileInsert = Inserts<'profiles'>
export type AnalysisTaskInsert = Inserts<'analysis_tasks'>
export type UserSettingsInsert = Inserts<'user_settings'>
export type SubscriptionInsert = Inserts<'subscriptions'>
export type UsageStatsInsert = Inserts<'usage_stats'>
export type ScheduledAnalysisInsert = Inserts<'scheduled_analyses'>
export type ApiKeyInsert = Inserts<'api_keys'>
export type WebhookInsert = Inserts<'webhooks'>

// Update types
export type ProfileUpdate = Updates<'profiles'>
export type AnalysisTaskUpdate = Updates<'analysis_tasks'>
export type UserSettingsUpdate = Updates<'user_settings'>
export type SubscriptionUpdate = Updates<'subscriptions'>
export type UsageStatsUpdate = Updates<'usage_stats'>
export type ScheduledAnalysisUpdate = Updates<'scheduled_analyses'>
export type ApiKeyUpdate = Updates<'api_keys'>
export type WebhookUpdate = Updates<'webhooks'>

// Enum types
export type SubscriptionTier = Enums<'subscription_tier'>
export type SubscriptionStatus = Enums<'subscription_status'>
export type AnalysisStatus = Enums<'analysis_status'>
export type AnalysisType = Enums<'analysis_type'>
export type Frequency = Enums<'frequency'>