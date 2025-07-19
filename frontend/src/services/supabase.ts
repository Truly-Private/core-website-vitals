import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { Database } from '@/types/supabase.types'

// Supabase configuration
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

// Create Supabase client
export const supabase: SupabaseClient<Database> = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
})

// Supabase service methods
export const supabaseService = {
  // Authentication
  auth: {
    signUp: async (email: string, password: string, metadata?: any) => {
      return await supabase.auth.signUp({
        email,
        password,
        options: {
          data: metadata,
        },
      })
    },
    
    signIn: async (email: string, password: string) => {
      return await supabase.auth.signInWithPassword({
        email,
        password,
      })
    },
    
    signOut: async () => {
      return await supabase.auth.signOut()
    },
    
    resetPassword: async (email: string) => {
      return await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })
    },
    
    updatePassword: async (password: string) => {
      return await supabase.auth.updateUser({ password })
    },
    
    getSession: async () => {
      return await supabase.auth.getSession()
    },
    
    getUser: async () => {
      return await supabase.auth.getUser()
    },
    
    onAuthStateChange: (callback: (event: any, session: any) => void) => {
      return supabase.auth.onAuthStateChange(callback)
    },
  },
  
  // Database operations
  database: {
    // Generic select
    select: <T = any>(
      table: string,
      columns = '*',
      filters?: Record<string, any>,
      options?: {
        orderBy?: { column: string; ascending?: boolean }
        limit?: number
        offset?: number
      }
    ) => {
      let query = supabase.from(table).select(columns)
      
      // Apply filters
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            query = query.eq(key, value)
          }
        })
      }
      
      // Apply options
      if (options?.orderBy) {
        query = query.order(options.orderBy.column, {
          ascending: options.orderBy.ascending ?? true,
        })
      }
      
      if (options?.limit) {
        query = query.limit(options.limit)
      }
      
      if (options?.offset) {
        query = query.range(options.offset, options.offset + (options.limit || 10) - 1)
      }
      
      return query
    },
    
    // Generic insert
    insert: <T = any>(table: string, data: T | T[]) => {
      return supabase.from(table).insert(data)
    },
    
    // Generic update
    update: <T = any>(table: string, data: Partial<T>, filters: Record<string, any>) => {
      let query = supabase.from(table).update(data)
      
      Object.entries(filters).forEach(([key, value]) => {
        query = query.eq(key, value)
      })
      
      return query
    },
    
    // Generic delete
    delete: (table: string, filters: Record<string, any>) => {
      let query = supabase.from(table).delete()
      
      Object.entries(filters).forEach(([key, value]) => {
        query = query.eq(key, value)
      })
      
      return query
    },
    
    // Generic upsert
    upsert: <T = any>(table: string, data: T | T[], onConflict?: string) => {
      return supabase.from(table).upsert(data, { onConflict })
    },
  },
  
  // Real-time subscriptions
  realtime: {
    subscribe: (
      table: string,
      callback: (payload: any) => void,
      options?: {
        event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*'
        schema?: string
        filter?: string
      }
    ) => {
      const channel = supabase
        .channel(`realtime:${table}`)
        .on(
          'postgres_changes',
          {
            event: options?.event || '*',
            schema: options?.schema || 'public',
            table,
            filter: options?.filter,
          },
          callback
        )
        .subscribe()
      
      return channel
    },
    
    unsubscribe: (channel: any) => {
      return supabase.removeChannel(channel)
    },
  },
  
  // Storage operations
  storage: {
    upload: async (bucket: string, path: string, file: File, options?: any) => {
      return await supabase.storage.from(bucket).upload(path, file, options)
    },
    
    download: async (bucket: string, path: string) => {
      return await supabase.storage.from(bucket).download(path)
    },
    
    getPublicUrl: (bucket: string, path: string) => {
      return supabase.storage.from(bucket).getPublicUrl(path)
    },
    
    remove: async (bucket: string, paths: string[]) => {
      return await supabase.storage.from(bucket).remove(paths)
    },
    
    list: async (bucket: string, path?: string, options?: any) => {
      return await supabase.storage.from(bucket).list(path, options)
    },
    
    createBucket: async (bucket: string, options?: any) => {
      return await supabase.storage.createBucket(bucket, options)
    },
    
    deleteBucket: async (bucket: string) => {
      return await supabase.storage.deleteBucket(bucket)
    },
  },
  
  // Edge functions
  functions: {
    invoke: async (functionName: string, options?: any) => {
      return await supabase.functions.invoke(functionName, options)
    },
  },
}

// Specific table helpers
export const profilesTable = {
  getProfile: async (userId: string) => {
    return await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single()
  },
  
  updateProfile: async (userId: string, updates: any) => {
    return await supabase
      .from('profiles')
      .update(updates)
      .eq('id', userId)
      .select()
      .single()
  },
  
  createProfile: async (profile: any) => {
    return await supabase
      .from('profiles')
      .insert(profile)
      .select()
      .single()
  },
}

export const analysisTasksTable = {
  getUserAnalyses: async (userId: string, options?: any) => {
    let query = supabase
      .from('analysis_tasks')
      .select('*')
      .eq('user_id', userId)
    
    if (options?.status) {
      query = query.eq('status', options.status)
    }
    
    if (options?.limit) {
      query = query.limit(options.limit)
    }
    
    if (options?.orderBy) {
      query = query.order(options.orderBy.column, {
        ascending: options.orderBy.ascending ?? false,
      })
    }
    
    return await query
  },
  
  getAnalysisById: async (id: string) => {
    return await supabase
      .from('analysis_tasks')
      .select('*')
      .eq('id', id)
      .single()
  },
  
  createAnalysis: async (analysis: any) => {
    return await supabase
      .from('analysis_tasks')
      .insert(analysis)
      .select()
      .single()
  },
  
  updateAnalysis: async (id: string, updates: any) => {
    return await supabase
      .from('analysis_tasks')
      .update(updates)
      .eq('id', id)
      .select()
      .single()
  },
  
  deleteAnalysis: async (id: string) => {
    return await supabase
      .from('analysis_tasks')
      .delete()
      .eq('id', id)
  },
  
  subscribeToUserAnalyses: (userId: string, callback: (payload: any) => void) => {
    return supabase
      .channel('analysis_tasks')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'analysis_tasks',
          filter: `user_id=eq.${userId}`,
        },
        callback
      )
      .subscribe()
  },
}

// Helper functions
export const helpers = {
  // Generate UUID
  generateUUID: () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0
      const v = c === 'x' ? r : (r & 0x3 | 0x8)
      return v.toString(16)
    })
  },
  
  // Format date
  formatDate: (date: string | Date) => {
    return new Date(date).toLocaleDateString()
  },
  
  // Format date time
  formatDateTime: (date: string | Date) => {
    return new Date(date).toLocaleString()
  },
  
  // Get time ago
  getTimeAgo: (date: string | Date) => {
    const now = new Date()
    const past = new Date(date)
    const diffMs = now.getTime() - past.getTime()
    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    } else if (diffMinutes > 0) {
      return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`
    } else {
      return 'Just now'
    }
  },
  
  // Check if user is authenticated
  isAuthenticated: async () => {
    const { data: { user } } = await supabase.auth.getUser()
    return !!user
  },
  
  // Get current user
  getCurrentUser: async () => {
    const { data: { user } } = await supabase.auth.getUser()
    return user
  },
  
  // Handle Supabase errors
  handleError: (error: any) => {
    console.error('Supabase error:', error)
    
    if (error.message) {
      return error.message
    }
    
    if (error.error_description) {
      return error.error_description
    }
    
    return 'An unexpected error occurred'
  },
}

export default supabaseService