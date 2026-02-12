import axios from 'axios';

/**
 * 智能分析 API 服务层
 * 
 * 提供与后端智能分析上下文的 REST API 交互和 WebSocket 实时通信功能。
 * 
 * API 端点：
 * - POST /api/intelligence/tasks/industry-research - 创建快速行业认知任务
 * - POST /api/intelligence/tasks/credibility-verification - 创建概念可信度验证任务
 * - GET /api/intelligence/tasks/<task_id> - 获取任务详情
 * - GET /api/intelligence/tasks - 获取任务列表
 * - POST /api/intelligence/tasks/<task_id>/cancel - 取消任务
 * 
 * WebSocket 事件：
 * - task_progress - 任务进度更新
 * - task_completed - 任务完成通知
 * - task_failed - 任务失败通知
 * 
 * Requirements: 9.1-9.6
 */

// 创建 axios 实例，复用现有配置
const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ============================================================================
// REST API 方法
// ============================================================================

/**
 * 智能分析 API 对象
 * 包含所有与智能分析相关的 REST API 方法
 */
export const intelligenceApi = {
  /**
   * 创建快速行业认知任务
   * 
   * @param {string} query - 用户查询文本，如"快速了解合成生物学赛道"
   * @returns {Promise<{data: {task_id: string}}>} 返回创建的任务 ID
   * @throws {Error} 当 query 为空时返回 400 错误
   * 
   * @example
   * const response = await intelligenceApi.createIndustryResearch('快速了解合成生物学赛道');
   * console.log(response.data.task_id); // 'uuid-xxxx-xxxx'
   */
  createIndustryResearch: (query) => 
    apiClient.post('/intelligence/tasks/industry-research', { query }),

  /**
   * 创建概念可信度验证任务
   * 
   * @param {string} stockCode - 股票代码，如 "600519.SH"
   * @param {string} concept - 要验证的概念，如 "AI+白酒"
   * @returns {Promise<{data: {task_id: string}}>} 返回创建的任务 ID
   * @throws {Error} 当 stockCode 或 concept 为空时返回 400 错误
   * 
   * @example
   * const response = await intelligenceApi.createCredibilityVerification('600519.SH', 'AI+白酒');
   * console.log(response.data.task_id); // 'uuid-xxxx-xxxx'
   */
  createCredibilityVerification: (stockCode, concept) => 
    apiClient.post('/intelligence/tasks/credibility-verification', { 
      stock_code: stockCode, 
      concept 
    }),

  /**
   * 获取任务详情
   * 
   * @param {string} taskId - 任务 ID
   * @returns {Promise<{data: TaskResponse}>} 返回任务详情
   * @throws {Error} 当任务不存在时返回 404 错误
   * 
   * @typedef {Object} TaskResponse
   * @property {string} task_id - 任务 ID
   * @property {string} task_type - 任务类型 ('industry_research' | 'credibility_verification')
   * @property {string} query - 查询内容
   * @property {string} status - 任务状态 ('pending' | 'running' | 'completed' | 'failed' | 'cancelled')
   * @property {number} progress - 进度 (0-100)
   * @property {Array<AgentStep>} agent_steps - Agent 执行步骤
   * @property {Object|null} result - 任务结果 (IndustryInsight 或 CredibilityReport)
   * @property {string|null} error_message - 错误信息
   * @property {string} created_at - 创建时间 (ISO 格式)
   * @property {string} updated_at - 更新时间 (ISO 格式)
   * @property {string|null} completed_at - 完成时间 (ISO 格式)
   * 
   * @example
   * const response = await intelligenceApi.getTask('uuid-xxxx-xxxx');
   * console.log(response.data.status); // 'running'
   */
  getTask: (taskId) => 
    apiClient.get(`/intelligence/tasks/${taskId}`),

  /**
   * 获取任务列表
   * 
   * @param {Object} [params] - 查询参数
   * @param {number} [params.limit=20] - 每页数量
   * @param {number} [params.offset=0] - 偏移量
   * @param {string} [params.status] - 按状态筛选
   * @param {string} [params.task_type] - 按任务类型筛选
   * @returns {Promise<{data: Array<TaskResponse>}>} 返回任务列表
   * 
   * @example
   * const response = await intelligenceApi.listTasks({ limit: 10, offset: 0 });
   * console.log(response.data.length); // 10
   */
  listTasks: (params) => 
    apiClient.get('/intelligence/tasks', { params }),

  /**
   * 取消任务
   * 
   * @param {string} taskId - 任务 ID
   * @returns {Promise<{data: {message: string}}>} 返回取消结果
   * @throws {Error} 当任务不存在时返回 404 错误
   * @throws {Error} 当任务状态不允许取消时返回 409 错误
   * 
   * @example
   * await intelligenceApi.cancelTask('uuid-xxxx-xxxx');
   */
  cancelTask: (taskId) => 
    apiClient.post(`/intelligence/tasks/${taskId}/cancel`),
};

// ============================================================================
// WebSocket 连接管理
// ============================================================================

/**
 * WebSocket 连接管理器
 * 
 * 使用 Socket.IO 客户端管理与后端的实时通信连接。
 * 支持任务进度更新和任务完成通知的实时推送。
 * 
 * 注意：需要安装 socket.io-client 依赖
 * npm install socket.io-client
 */

// WebSocket 连接实例
let socket = null;

// 事件回调存储
const eventCallbacks = {
  task_progress: [],
  task_completed: [],
  task_failed: [],
  connect: [],
  disconnect: [],
  error: [],
};

/**
 * 建立 WebSocket 连接
 * 
 * @param {Object} [options] - 连接选项
 * @param {string} [options.url] - WebSocket 服务器 URL，默认为当前域名
 * @param {string} [options.namespace='/intelligence'] - Socket.IO 命名空间
 * @param {Object} [options.auth] - 认证信息
 * @returns {Promise<void>} 连接成功后 resolve
 * 
 * @example
 * await connectWebSocket();
 * // 或指定选项
 * await connectWebSocket({ url: 'http://localhost:5000', namespace: '/intelligence' });
 */
export async function connectWebSocket(options = {}) {
  // 如果已连接，直接返回
  if (socket && socket.connected) {
    console.log('[WebSocket] Already connected');
    return;
  }

  // 动态导入 socket.io-client（支持按需加载）
  let io;
  try {
    const socketIO = await import('socket.io-client');
    io = socketIO.io || socketIO.default;
  } catch (error) {
    console.error('[WebSocket] Failed to load socket.io-client. Please install it: npm install socket.io-client');
    throw new Error('socket.io-client not installed. Run: npm install socket.io-client');
  }

  const {
    url = window.location.origin,
    namespace = '/intelligence',
    auth = {},
  } = options;

  return new Promise((resolve, reject) => {
    try {
      // 创建 Socket.IO 连接
      socket = io(`${url}${namespace}`, {
        transports: ['websocket', 'polling'],
        auth,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000,
      });

      // 连接成功
      socket.on('connect', () => {
        console.log('[WebSocket] Connected to server');
        eventCallbacks.connect.forEach(cb => cb());
        resolve();
      });

      // 连接错误
      socket.on('connect_error', (error) => {
        console.error('[WebSocket] Connection error:', error.message);
        eventCallbacks.error.forEach(cb => cb(error));
        reject(error);
      });

      // 断开连接
      socket.on('disconnect', (reason) => {
        console.log('[WebSocket] Disconnected:', reason);
        eventCallbacks.disconnect.forEach(cb => cb(reason));
      });

      // 任务进度更新事件
      socket.on('task_progress', (data) => {
        console.log('[WebSocket] Task progress:', data);
        eventCallbacks.task_progress.forEach(cb => cb(data));
      });

      // 任务完成事件
      socket.on('task_completed', (data) => {
        console.log('[WebSocket] Task completed:', data);
        eventCallbacks.task_completed.forEach(cb => cb(data));
      });

      // 任务失败事件
      socket.on('task_failed', (data) => {
        console.log('[WebSocket] Task failed:', data);
        eventCallbacks.task_failed.forEach(cb => cb(data));
      });

    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
      reject(error);
    }
  });
}

/**
 * 断开 WebSocket 连接
 * 
 * @example
 * disconnectWebSocket();
 */
export function disconnectWebSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
    console.log('[WebSocket] Disconnected');
  }
}

/**
 * 检查 WebSocket 是否已连接
 * 
 * @returns {boolean} 是否已连接
 * 
 * @example
 * if (isWebSocketConnected()) {
 *   console.log('WebSocket is connected');
 * }
 */
export function isWebSocketConnected() {
  return socket !== null && socket.connected;
}

/**
 * 订阅任务进度更新事件
 * 
 * @param {Function} callback - 回调函数，接收进度数据
 * @returns {Function} 取消订阅函数
 * 
 * @typedef {Object} TaskProgressData
 * @property {string} task_id - 任务 ID
 * @property {number} progress - 当前进度 (0-100)
 * @property {AgentStep} agent_step - 当前 Agent 步骤信息
 * 
 * @typedef {Object} AgentStep
 * @property {string} agent_name - Agent 名称
 * @property {string} status - 状态 ('pending' | 'running' | 'completed' | 'failed' | 'skipped')
 * @property {string|null} started_at - 开始时间 (ISO 格式)
 * @property {string|null} completed_at - 完成时间 (ISO 格式)
 * @property {string|null} output_summary - 输出摘要
 * @property {string|null} error_message - 错误信息
 * 
 * @example
 * const unsubscribe = onTaskProgress((data) => {
 *   console.log(`Task ${data.task_id} progress: ${data.progress}%`);
 *   console.log(`Current agent: ${data.agent_step.agent_name}`);
 * });
 * 
 * // 取消订阅
 * unsubscribe();
 */
export function onTaskProgress(callback) {
  if (typeof callback !== 'function') {
    throw new Error('callback must be a function');
  }
  
  eventCallbacks.task_progress.push(callback);
  
  // 返回取消订阅函数
  return () => {
    const index = eventCallbacks.task_progress.indexOf(callback);
    if (index > -1) {
      eventCallbacks.task_progress.splice(index, 1);
    }
  };
}

/**
 * 订阅任务完成事件
 * 
 * @param {Function} callback - 回调函数，接收完成数据
 * @returns {Function} 取消订阅函数
 * 
 * @typedef {Object} TaskCompletedData
 * @property {string} task_id - 任务 ID
 * @property {Object} result - 任务结果 (IndustryInsight 或 CredibilityReport)
 * 
 * @example
 * const unsubscribe = onTaskCompleted((data) => {
 *   console.log(`Task ${data.task_id} completed!`);
 *   console.log('Result:', data.result);
 * });
 * 
 * // 取消订阅
 * unsubscribe();
 */
export function onTaskCompleted(callback) {
  if (typeof callback !== 'function') {
    throw new Error('callback must be a function');
  }
  
  eventCallbacks.task_completed.push(callback);
  
  // 返回取消订阅函数
  return () => {
    const index = eventCallbacks.task_completed.indexOf(callback);
    if (index > -1) {
      eventCallbacks.task_completed.splice(index, 1);
    }
  };
}

/**
 * 订阅任务失败事件
 * 
 * @param {Function} callback - 回调函数，接收失败数据
 * @returns {Function} 取消订阅函数
 * 
 * @typedef {Object} TaskFailedData
 * @property {string} task_id - 任务 ID
 * @property {string} error - 错误信息
 * 
 * @example
 * const unsubscribe = onTaskFailed((data) => {
 *   console.log(`Task ${data.task_id} failed: ${data.error}`);
 * });
 * 
 * // 取消订阅
 * unsubscribe();
 */
export function onTaskFailed(callback) {
  if (typeof callback !== 'function') {
    throw new Error('callback must be a function');
  }
  
  eventCallbacks.task_failed.push(callback);
  
  // 返回取消订阅函数
  return () => {
    const index = eventCallbacks.task_failed.indexOf(callback);
    if (index > -1) {
      eventCallbacks.task_failed.splice(index, 1);
    }
  };
}

/**
 * 订阅连接事件
 * 
 * @param {Function} callback - 回调函数
 * @returns {Function} 取消订阅函数
 * 
 * @example
 * const unsubscribe = onConnect(() => {
 *   console.log('WebSocket connected!');
 * });
 */
export function onConnect(callback) {
  if (typeof callback !== 'function') {
    throw new Error('callback must be a function');
  }
  
  eventCallbacks.connect.push(callback);
  
  return () => {
    const index = eventCallbacks.connect.indexOf(callback);
    if (index > -1) {
      eventCallbacks.connect.splice(index, 1);
    }
  };
}

/**
 * 订阅断开连接事件
 * 
 * @param {Function} callback - 回调函数，接收断开原因
 * @returns {Function} 取消订阅函数
 * 
 * @example
 * const unsubscribe = onDisconnect((reason) => {
 *   console.log('WebSocket disconnected:', reason);
 * });
 */
export function onDisconnect(callback) {
  if (typeof callback !== 'function') {
    throw new Error('callback must be a function');
  }
  
  eventCallbacks.disconnect.push(callback);
  
  return () => {
    const index = eventCallbacks.disconnect.indexOf(callback);
    if (index > -1) {
      eventCallbacks.disconnect.splice(index, 1);
    }
  };
}

/**
 * 订阅错误事件
 * 
 * @param {Function} callback - 回调函数，接收错误对象
 * @returns {Function} 取消订阅函数
 * 
 * @example
 * const unsubscribe = onError((error) => {
 *   console.error('WebSocket error:', error);
 * });
 */
export function onError(callback) {
  if (typeof callback !== 'function') {
    throw new Error('callback must be a function');
  }
  
  eventCallbacks.error.push(callback);
  
  return () => {
    const index = eventCallbacks.error.indexOf(callback);
    if (index > -1) {
      eventCallbacks.error.splice(index, 1);
    }
  };
}

/**
 * 加入任务房间（用于接收特定任务的更新）
 * 
 * @param {string} taskId - 任务 ID
 * 
 * @example
 * joinTaskRoom('uuid-xxxx-xxxx');
 */
export function joinTaskRoom(taskId) {
  if (!socket || !socket.connected) {
    console.warn('[WebSocket] Not connected. Call connectWebSocket() first.');
    return;
  }
  
  socket.emit('join_task', { task_id: taskId });
  console.log(`[WebSocket] Joined task room: ${taskId}`);
}

/**
 * 离开任务房间
 * 
 * @param {string} taskId - 任务 ID
 * 
 * @example
 * leaveTaskRoom('uuid-xxxx-xxxx');
 */
export function leaveTaskRoom(taskId) {
  if (!socket || !socket.connected) {
    console.warn('[WebSocket] Not connected.');
    return;
  }
  
  socket.emit('leave_task', { task_id: taskId });
  console.log(`[WebSocket] Left task room: ${taskId}`);
}

// ============================================================================
// WebSocket 工具对象（便于统一导入）
// ============================================================================

/**
 * WebSocket 工具对象
 * 包含所有 WebSocket 相关的方法
 */
export const intelligenceWebSocket = {
  connect: connectWebSocket,
  disconnect: disconnectWebSocket,
  isConnected: isWebSocketConnected,
  onTaskProgress,
  onTaskCompleted,
  onTaskFailed,
  onConnect,
  onDisconnect,
  onError,
  joinTaskRoom,
  leaveTaskRoom,
};

// 默认导出
export default {
  ...intelligenceApi,
  ...intelligenceWebSocket,
};
