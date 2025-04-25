# aiagent-enterprise-practise
AI Agent企业级实践

## 导入包

```bash
python -m pip install -e . --no-deps
```
## 设置环境变量
```bash
# 设置当前项目路径为根目录（当前终端会话有效）
export PYTHONPATH=/Users/caojm/projects/ai/aiagent-enterprise-practise
```

## 运行
```bash
python -m agent.flight.flight_assistant_v0
```

## 空间态势智能体 API 示例

### 1. 查询场景是否存在
```bash
curl -X POST "http://localhost:8028/api/v1/space/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "查询场景是否存在：空间站演示场景", 
    "thread_id": "test-thread-002"
  }'
```

### 2. 创建场景
```bash
curl -X POST "http://localhost:8028/api/v1/space/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "你好", 
    "thread_id": "test-thread-002"
  }'
```

```bash
curl -X POST "http://localhost:8028/api/v1/space/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "我要创建一个场景，名称为空间站演示场景, 地球", 
    "thread_id": "test-thread-002"
  }'
```

```bash
curl -X POST "http://localhost:8028/api/v1/space/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "前年5月4日到前年5月5日", 
    "thread_id": "test-thread-002"
  }'
```

### 3. 添加卫星实体
```bash
curl -X POST "http://localhost:8028/api/v1/space/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "请在空间站演示场景中添加卫星，编号SL-44291，起止时间2024-01-01T00:00:00Z到2024-01-02T00:00:00Z，TLE数据如下：1 44291U 19029A   24060.53167824  .00000023  00000+0  00000+0 0  9993\n2 44291  97.9000  80.0000 0010000  90.0000 270.0000 15.00000000    01", 
    "thread_id": "test-thread-002"
  }'
```
