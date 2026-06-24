/**
 * Axios 请求封装
 * 统一处理请求/响应拦截，全局错误提示
 * 无 Token 认证，适用于开放系统
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 Axios 实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 120000 // 请求超时时间 120 秒（原 30 秒）
})

// 请求拦截器（可添加 Token、Loading 等）
service.interceptors.request.use(
  (config) => {
    // 无需添加 token，直接返回配置
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端返回格式：{ code: 200, data: ..., message: ... }
    // 如果 code 存在且不为 200，视为业务错误
    if (res.code !== undefined && res.code !== 200) {
      ElMessage.error(res.message || '系统异常')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    // 成功返回 data 部分
    return res
  },
  (error) => {
    console.error('响应错误:', error)
    ElMessage.error(error.message || '网络异常')
    return Promise.reject(error)
  }
)

export default service