/**
 * Supabase real-time subscriptions for Core Website Vitals
 * Handles real-time database changes via Supabase subscriptions
 */
import { supabase } from './supabase'
import { useAuthStore } from '@/stores/auth'
import { useAnalysisStore } from '@/stores/analysis'
import { useUIStore } from '@/stores/ui'
import type { AnalysisTask } from '@/types/analysis.types'
import type { RealtimeChannel } from '@supabase/supabase-js'

export interface SupabaseRealtimeConfig {
  enableAnalysisUpdates: boolean
  enableProfileUpdates: boolean
  enableNotifications: boolean
}

export class SupabaseRealtimeService {
  private channels: Map<string, RealtimeChannel> = new Map()
  private authStore = useAuthStore()
  private analysisStore = useAnalysisStore()
  private uiStore = useUIStore()
  private config: SupabaseRealtimeConfig = {
    enableAnalysisUpdates: true,
    enableProfileUpdates: true,
    enableNotifications: true
  }

  constructor(config?: Partial<SupabaseRealtimeConfig>) {
    if (config) {
      this.config = { ...this.config, ...config }
    }
  }

  /**
   * Subscribe to analysis task updates for the current user
   */
  public subscribeToAnalysisUpdates() {
    if (!this.config.enableAnalysisUpdates || !this.authStore.user) {
      return
    }

    const userId = this.authStore.user.id
    const channelName = `analysis_updates_${userId}`

    if (this.channels.has(channelName)) {
      return // Already subscribed
    }

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'analysis_tasks',
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          this.handleAnalysisChange(payload)
        }
      )
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log('Subscribed to analysis updates')
        } else if (status === 'CLOSED') {
          console.log('Analysis updates subscription closed')
        } else if (status === 'CHANNEL_ERROR') {
          console.error('Error subscribing to analysis updates')
          this.uiStore.showNotification(
            'Failed to connect to real-time updates',
            'warning',
            5000
          )
        }
      })

    this.channels.set(channelName, channel)
  }

  /**
   * Subscribe to user profile updates
   */
  public subscribeToProfileUpdates() {
    if (!this.config.enableProfileUpdates || !this.authStore.user) {
      return
    }

    const userId = this.authStore.user.id
    const channelName = `profile_updates_${userId}`

    if (this.channels.has(channelName)) {
      return // Already subscribed
    }

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'profiles',
          filter: `id=eq.${userId}`
        },
        (payload) => {
          this.handleProfileChange(payload)
        }
      )
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log('Subscribed to profile updates')
        } else if (status === 'CLOSED') {
          console.log('Profile updates subscription closed')
        } else if (status === 'CHANNEL_ERROR') {
          console.error('Error subscribing to profile updates')
        }
      })

    this.channels.set(channelName, channel)
  }

  /**
   * Subscribe to system notifications
   */
  public subscribeToNotifications() {
    if (!this.config.enableNotifications || !this.authStore.user) {
      return
    }

    const userId = this.authStore.user.id
    const channelName = `notifications_${userId}`

    if (this.channels.has(channelName)) {
      return // Already subscribed
    }

    // Note: This would require a notifications table in the database
    // For now, we'll implement a placeholder
    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          this.handleNotificationChange(payload)
        }
      )
      .subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.log('Subscribed to notifications')
        } else if (status === 'CLOSED') {
          console.log('Notifications subscription closed')
        } else if (status === 'CHANNEL_ERROR') {
          console.error('Error subscribing to notifications')
        }
      })

    this.channels.set(channelName, channel)
  }

  /**
   * Subscribe to all real-time updates
   */
  public subscribeToAll() {
    this.subscribeToAnalysisUpdates()
    this.subscribeToProfileUpdates()
    this.subscribeToNotifications()
  }

  /**
   * Unsubscribe from specific channel
   */
  public unsubscribe(channelName: string) {
    const channel = this.channels.get(channelName)
    if (channel) {
      supabase.removeChannel(channel)
      this.channels.delete(channelName)
    }
  }

  /**
   * Unsubscribe from all channels
   */
  public unsubscribeAll() {
    for (const [channelName, channel] of this.channels) {
      supabase.removeChannel(channel)
    }
    this.channels.clear()
  }

  /**
   * Handle analysis task changes
   */
  private handleAnalysisChange(payload: any) {
    const { eventType, new: newRecord, old: oldRecord } = payload

    try {
      switch (eventType) {
        case 'INSERT':
          this.analysisStore.addAnalysisTask(newRecord as AnalysisTask)
          break

        case 'UPDATE':
          this.analysisStore.updateAnalysisTask(newRecord as AnalysisTask)
          
          // Show notification for status changes
          if (oldRecord?.status !== newRecord?.status) {
            this.handleAnalysisStatusChange(newRecord, oldRecord)
          }
          break

        case 'DELETE':
          this.analysisStore.removeAnalysisTask(oldRecord.id)
          break

        default:
          console.warn('Unknown analysis change event type:', eventType)
      }
    } catch (error) {
      console.error('Error handling analysis change:', error)
    }
  }

  /**
   * Handle analysis status changes
   */
  private handleAnalysisStatusChange(newRecord: AnalysisTask, oldRecord: AnalysisTask) {
    const url = newRecord.url_analyzed
    const shortUrl = url.length > 50 ? url.substring(0, 50) + '...' : url

    switch (newRecord.status) {
      case 'IN_PROGRESS':
        this.uiStore.showNotification(
          `Analysis started for ${shortUrl}`,
          'info',
          3000
        )
        break

      case 'SUCCESS':
        this.uiStore.showNotification(
          `Analysis completed for ${shortUrl}`,
          'success',
          5000
        )
        break

      case 'FAILED':
        this.uiStore.showNotification(
          `Analysis failed for ${shortUrl}`,
          'error',
          0
        )
        break

      case 'CANCELLED':
        this.uiStore.showNotification(
          `Analysis cancelled for ${shortUrl}`,
          'warning',
          3000
        )
        break

      default:
        break
    }
  }

  /**
   * Handle profile changes
   */
  private handleProfileChange(payload: any) {
    const { eventType, new: newRecord } = payload

    try {
      switch (eventType) {
        case 'UPDATE':
          // Update the user in auth store
          this.authStore.updateUser(newRecord)
          
          this.uiStore.showNotification(
            'Profile updated successfully',
            'success',
            3000
          )
          break

        default:
          console.warn('Unknown profile change event type:', eventType)
      }
    } catch (error) {
      console.error('Error handling profile change:', error)
    }
  }

  /**
   * Handle notification changes
   */
  private handleNotificationChange(payload: any) {
    const { eventType, new: newRecord } = payload

    try {
      switch (eventType) {
        case 'INSERT':
          // Show the notification
          this.uiStore.showNotification(
            newRecord.message,
            newRecord.type || 'info',
            newRecord.duration || 5000
          )
          break

        default:
          console.warn('Unknown notification change event type:', eventType)
      }
    } catch (error) {
      console.error('Error handling notification change:', error)
    }
  }

  /**
   * Get connection status
   */
  public getConnectionStatus(): Record<string, string> {
    const status: Record<string, string> = {}
    
    for (const [channelName, channel] of this.channels) {
      status[channelName] = channel.state
    }
    
    return status
  }

  /**
   * Check if connected to any channels
   */
  public get isConnected(): boolean {
    return Array.from(this.channels.values()).some(
      channel => channel.state === 'joined'
    )
  }
}

// Global instance
export const supabaseRealtimeService = new SupabaseRealtimeService()

// Vue plugin
export default {
  install(app: any) {
    app.config.globalProperties.$supabaseRealtime = supabaseRealtimeService
    app.provide('supabaseRealtime', supabaseRealtimeService)
  }
}

// Composable for easier use in components
export function useSupabaseRealtime() {
  return supabaseRealtimeService
}