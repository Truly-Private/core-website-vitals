/**
 * Real-time WebSocket service for Core Website Vitals
 * Handles WebSocket connections and real-time updates
 */
import { useAuthStore } from '@/stores/auth'
import { useAnalysisStore } from '@/stores/analysis'
import { useUIStore } from '@/stores/ui'
import type { AnalysisTask } from '@/types/analysis.types'

export interface WebSocketMessage {
  type: 'analysis_update' | 'analysis_progress' | 'analysis_complete' | 'analysis_failed' | 'notification' | 'user_activity' | 'heartbeat' | 'error'
  data: any
  timestamp: string
  user_id?: string
  analysis_id?: string
}

export interface AnalysisProgress {
  analysis_id: string
  progress: number
  stage: string
  details?: string
  timestamp: string
}

export interface NotificationData {
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp: string
}

export class RealtimeService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private heartbeatInterval: NodeJS.Timeout | null = null
  private isConnected = false
  private subscribedAnalyses = new Set<string>()
  private messageHandlers = new Map<string, Function[]>()
  private authStore = useAuthStore()
  private analysisStore = useAnalysisStore()
  private uiStore = useUIStore()

  constructor() {
    this.setupEventHandlers()
  }

  private setupEventHandlers() {
    // Handle analysis updates
    this.on('analysis_update', (data: any) => {
      this.analysisStore.updateAnalysisFromRealtime(data)
    })

    // Handle analysis progress
    this.on('analysis_progress', (data: AnalysisProgress) => {
      this.analysisStore.updateAnalysisProgress(data.analysis_id, data)
      
      // Show progress notification
      this.uiStore.showNotification(
        `Analysis ${data.progress}% complete - ${data.stage}`,
        'info',
        3000
      )
    })

    // Handle analysis completion
    this.on('analysis_complete', (data: any) => {
      this.analysisStore.updateAnalysisFromRealtime(data)
      
      // Show completion notification
      this.uiStore.showNotification(
        'Analysis completed successfully!',
        'success',
        5000
      )
    })

    // Handle analysis failure
    this.on('analysis_failed', (data: any) => {
      this.analysisStore.updateAnalysisFromRealtime(data)
      
      // Show failure notification
      this.uiStore.showNotification(
        `Analysis failed: ${data.error}`,
        'error',
        0
      )
    })

    // Handle notifications
    this.on('notification', (data: NotificationData) => {
      this.uiStore.showNotification(
        data.message,
        data.type,
        data.type === 'error' ? 0 : 5000
      )
    })

    // Handle heartbeat
    this.on('heartbeat', () => {
      // Heartbeat received, connection is alive
    })

    // Handle errors
    this.on('error', (data: any) => {
      console.error('WebSocket error:', data)
      this.uiStore.showNotification(
        'Connection error occurred',
        'error',
        3000
      )
    })
  }

  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      const token = this.authStore.accessToken
      if (!token) {
        reject(new Error('No access token available'))
        return
      }

      const wsUrl = this.getWebSocketUrl(token)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.isConnected = true
        this.reconnectAttempts = 0
        this.startHeartbeat()
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        this.isConnected = false
        this.stopHeartbeat()
        
        if (event.code !== 1000) { // Not a normal closure
          this.handleReconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnected = false
        reject(error)
      }
    })
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Normal closure')
      this.ws = null
    }
    this.isConnected = false
    this.stopHeartbeat()
    this.subscribedAnalyses.clear()
  }

  public send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }

  public subscribeToAnalysis(analysisId: string) {
    if (!this.subscribedAnalyses.has(analysisId)) {
      this.subscribedAnalyses.add(analysisId)
      this.send({
        type: 'subscribe_analysis',
        analysis_id: analysisId
      })
    }
  }

  public unsubscribeFromAnalysis(analysisId: string) {
    if (this.subscribedAnalyses.has(analysisId)) {
      this.subscribedAnalyses.delete(analysisId)
      this.send({
        type: 'unsubscribe_analysis',
        analysis_id: analysisId
      })
    }
  }

  public on(event: string, handler: Function) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, [])
    }
    this.messageHandlers.get(event)!.push(handler)
  }

  public off(event: string, handler: Function) {
    const handlers = this.messageHandlers.get(event)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  public get connected(): boolean {
    return this.isConnected
  }

  private getWebSocketUrl(token: string): string {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    const wsUrl = baseUrl.replace(/^https?:\/\//, 'ws://').replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://')
    return `${wsUrl}/websocket/ws/${token}`
  }

  private handleMessage(message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data)
        } catch (error) {
          console.error(`Error handling message type ${message.type}:`, error)
        }
      })
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`)
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error)
        })
      }, delay)
    } else {
      console.error('Max reconnection attempts reached')
      this.uiStore.showNotification(
        'Connection lost. Please refresh the page.',
        'error',
        0
      )
    }
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({
          type: 'heartbeat',
          timestamp: new Date().toISOString()
        })
      }
    }, 30000) // Send heartbeat every 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

// Global instance
export const realtimeService = new RealtimeService()

// Vue plugin
export default {
  install(app: any) {
    app.config.globalProperties.$realtime = realtimeService
    app.provide('realtime', realtimeService)
  }
}

// Composable for easier use in components
export function useRealtime() {
  return realtimeService
}