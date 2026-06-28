# 飞书多 Bot 并发限流修复指南

## 适用场景
- OpenClaw 配置了 **多个飞书 bot**（>10 个）
- Gateway 启动后，bot **不回复消息**（私聊和群聊）
- 日志中有大量 `ECONNRESET` / `ECONNABORTED` / `probe timed out`

## 根本原因
46 个 bot 同时向 `open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal` 请求 token，触发飞书 API 限流。

**日志特征**：
```
feishu[bot-name]: bot info probe timed out after 30000ms; retry 1/3 in 5000ms
AxiosError: timeout of 30000ms exceeded
cause: ClientRequestError: socket hang up
cause: Error: read ECONNRESET
```

## 修复步骤

### 步骤 1：修改 `monitor.ts`（错开 bot 启动时间）

**文件**：`app/core/node_modules/openclaw/extensions/feishu/src/monitor.ts`

**在文件顶部添加**：
```typescript
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let _startupCounter = 0;

async function staggerStart(): Promise<number> {
  const myIndex = _startupCounter++;
  if (myIndex > 0) {
    await sleep(myIndex * 2000);  // 每个 bot 错开 2 秒
  }
  return myIndex;
}
```

**修改 `monitorFeishuProvider` 函数**（在 `if (opts.accountId)` 分支内）：
```typescript
if (opts.accountId) {
  const myIndex = await staggerStart();
  console.log(`[feishu-stagger] account=${opts.accountId} index=${myIndex} starting after ${myIndex * 2000}ms delay`);

  const account = resolveFeishuAccount({ cfg, accountId: opts.accountId });
  if (!account.enabled || !account.configured) {
    throw new Error(`Feishu account "${opts.accountId}" not configured or disabled`);
  }

  const { botOpenId, botName } = await fetchBotIdentityForMonitor(account, {
    runtime: opts.runtime,
    abortSignal: opts.abortSignal,
  });

  return monitorSingleAccount({
    cfg,
    account,
    runtime: opts.runtime,
    abortSignal: opts.abortSignal,
    botOpenIdSource: { kind: "prefetched", botOpenId, botName },
  });
}
```

---

### 步骤 2：修改 `monitor.startup.ts`（避免 retry 同步）

**文件**：`app/core/node_modules/openclaw/extensions/feishu/src/monitor.startup.ts`

**在文件顶部添加**：
```typescript
const FEISHU_STARTUP_BOT_INFO_RETRY_JITTER_MAX_MS = 5_000;
```

**修改 retry 逻辑**（在 `fetchBotIdentityForMonitor` 函数内）：
```typescript
if (isTimeout && !isLastAttempt) {
  const jitteredDelay = retryDelayMs + Math.floor(Math.random() * FEISHU_STARTUP_BOT_INFO_RETRY_JITTER_MAX_MS);
  error(
    `feishu[${account.accountId}]: bot info probe timed out after ${timeoutMs}ms; ` +
      `retry ${attempt + 1}/${maxRetries} in ${jitteredDelay}ms`,
  );
  await sleep(jitteredDelay);
  continue;
}
```

---

### 步骤 3：修改 `client.ts`（共享 Lark client）

**文件**：`app/core/node_modules/openclaw/extensions/feishu/src/client.ts`

**修改 `createFeishuClient` 函数**：
```typescript
const cacheKey = appId;  // 改用 appId 作为缓存键（原来是 accountId）

const cached = clientCache.get(cacheKey);
if (
  cached &&
  cached.config.appId === appId &&
  cached.config.appSecret === appSecret &&
  cached.config.domain === domain &&
  cached.config.httpTimeoutMs === defaultHttpTimeoutMs
) {
  return cached.client;
}

// ... 创建新 client ...

clientCache.set(cacheKey, {  // 改用 cacheKey（即 appId）
  config: { appId, appSecret, domain, httpTimeoutMs: defaultHttpTimeoutMs },
  client,
});
```

---

### 步骤 4：清除缓存并重启

```bash
# 清除 jiti TypeScript 缓存（否则修改不生效）
rm -rf "/tmp/jiti/"

# 清除旧日志和锁文件
rm -f "/tmp/openclaw/gateway."*.lock
rm -f "data/logs/gateway.log"

# 启动 Gateway
export OPENCLAW_HOME="data"
export OPENCLAW_STATE_DIR="data/.openclaw"
export OPENCLAW_CONFIG_PATH="data/.openclaw/openclaw.json"
export NO_PROXY="127.0.0.1,localhost,open.feishu.cn,feishu.cn"

cd "app/core"
"app/runtime/node-win-x64/node.exe" \
  "app/core/node_modules/openclaw/openclaw.mjs" \
  gateway --port 18790 &> "data/logs/gateway.log" &
```

---

### 步骤 5：验证修复效果

```bash
# 等待 2 分钟让所有 bot 启动完成
sleep 120

# 检查 probe 错误数（应该是 0）
grep -c "probe timed out" "data/logs/gateway.log"

# 检查已连接的 bot 数
grep -c "client ready" "data/logs/gateway.log"

# Health check
curl -s http://127.0.0.1:18790/health
```

**预期结果**：
- ✅ Probe 错误数 = 0
- ✅ "client ready" 数 = 配置的 bot 数
- ✅ Health check 返回 `{"ok":true,"status":"live"}`

---

## 优化建议

### 减少启动时间
如果 46 个 bot 串行启动太慢（~90 秒），可以将延迟从 2000ms 降至 500ms：
```typescript
await sleep(myIndex * 500);  // 总时间降至 ~23 秒
```

**注意**：延迟太短可能还是触发限流，建议从 2000ms 开始测试，逐步降低。

### 只启用必要的 bot
如果某些 bot 不常用，可以在 `openclaw.json` 中临时禁用：
```json
{
  "feishu": {
    "accounts": {
      "bot-name": {
        "enabled": false
      }
    }
  }
}
```

---

## 常见问题

**Q: 修改后还是全部失败？**
A: 检查 jiti 缓存是否清除（`/tmp/jiti/`），以及 `NO_PROXY` 是否包含飞书域名。

**Q: 部分 bot 还是失败？**
A: 可能是这些 bot 的 `appId` 不同（各自独立），导致 token 请求还是并发了。尝试增加延迟时间（2000ms → 3000ms）。

**Q: 启动后群聊回复慢？**
A: 可能是后面的 bot 还没完全启动。检查日志确认所有 bot 都已 "client ready"。

---

## 适用版本
- OpenClaw v1.1.x
- 飞书开放平台 API v3

## 作者
执中 @ 行知阁团队  
最后更新：2026-06-15
