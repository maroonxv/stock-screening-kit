/**
 * Screening Context WebSocket 客户端
 *
 * 连接 /screening 命名空间，接收任务进度、完成、失败等事件。
 *
 * Requirements: 7.2
 */
import { io } from 'socket.io-client';

class ScreeningSocket {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect() {
    if (this.socket?.connected) return;

    this.socket = io('/screening', {
      transports: ['websocket', 'polling'],
    });

    this.socket.on('task_progress', (data) => this._dispatch('progress', data));
    this.socket.on('task_completed', (data) => this._dispatch('completed', data));
    this.socket.on('task_failed', (data) => this._dispatch('failed', data));
    this.socket.on('task_status_changed', (data) => this._dispatch('status', data));
  }

  subscribe(taskId, callbacks) {
    this.listeners.set(taskId, callbacks);
  }

  unsubscribe(taskId) {
    this.listeners.delete(taskId);
  }

  _dispatch(event, data) {
    const callbacks = this.listeners.get(data.task_id);
    if (callbacks?.[event]) {
      callbacks[event](data);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }
}

export const screeningSocket = new ScreeningSocket();
