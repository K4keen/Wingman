# 笔记 01：API 骨架（config / db / main）

从代码里的 TODO 引导注释整理出来，复习和准备面试用。

## 配置（`app/config.py`）

**为什么不把数据库地址写死在代码里？**
同一份代码要跑在三个地方：本机、GitHub CI、Vultr 服务器，三处的地址和密码都不同。
写死的话，每换一个环境就要改代码，密码还会进 git。
所以代码只声明"我需要 `DATABASE_URL`"，值由环境变量提供：本地来自 `.env`，服务器上由 compose 注入。
这就是 12-factor 的配置原则。

**pydantic-settings 做了什么**：按字段名（不区分大小写）从环境变量和 `.env` 里读值，并转换类型。
缺了必填字段或类型不对，启动时直接报错。配置错误在启动那一刻暴露，不会跑到一半才发现。

**`.env` 路径**：`env_file=".env"` 是相对于"当前工作目录"的，从 `backend/` 启动就找不到根目录的 `.env`。
用 `Path(__file__).resolve().parents[2]` 从文件自身位置往上找，不受从哪里启动的影响。

**`extra="ignore"`**：`.env` 里还有 `POSTGRES_USER` 这类 Settings 没声明的变量，默认会报错，所以设成忽略。

**模块级单例 `settings`**：整个程序只读一次 `.env`，各处拿到的是同一份配置。

## 数据库（`app/db.py`）

**engine 和 session 为什么分开？**
建一条 TCP 连接很贵：握手加认证，要几毫秒到几十毫秒。
- **engine** = 连接池。启动时创建一次，全局共用，里面维护一批已建好的连接。
- **session** = 一个工作单元。每个请求开一个，从池子里借连接执行 SQL、管理事务，关闭时归还连接。

类比：engine 是车队，session 是一次叫车。

**为什么用 async**：等数据库返回的时候，事件循环可以去处理别的请求。
用同步驱动的话，整个线程会被卡住。URL 里的 `+asyncpg` 指定用异步驱动。

**`pool_pre_ping=True`**：借出连接前先 ping 一下，避免拿到已经断开的连接。
**`pool_size`**：常驻连接数，第 5 周压测时会回来调。

**`expire_on_commit=False`**：默认情况下，commit 之后对象的属性会被标记为过期，下次访问会偷偷再查一次数据库。
在 async 里这种隐式查询会抛 `MissingGreenlet`，关掉这个选项后，commit 之后对象的数据还能直接用。

**`get_session` 为什么用 yield**：yield 之前开 session，yield 出去的值交给路由用，yield 之后（请求结束）关 session。
`async with` 保证即使路由抛了异常，session 也会被关闭。

## 入口（`app/main.py`）

**uvicorn 和 FastAPI 的关系**：uvicorn 是服务器，负责监听端口，再按 ASGI 协议把请求交给 FastAPI。
FastAPI 只负责路由和处理请求。类比：uvicorn 是前台接电话，FastAPI 是后厨。

**lifespan**：yield 之前在启动时执行，yield 之后在关闭时执行。
和 `get_session` 是同一个套路，只是范围从一个请求变成整个程序。
`engine.dispose()` 负责正常关掉池子里的所有连接。

**健康检查**：负载均衡器、Docker 或监控系统会定期请求 `/health`。
返回 200 就继续给这个实例发流量，返回 503 就摘掉它或者重启它。
只返回 "ok" 没有意义，因为进程活着不代表能干活，所以要真的查一次数据库。

**`text("SELECT 1")`**：SQLAlchemy 2.0 不接受裸字符串 SQL，强制你声明"这是原始 SQL"，防止把用户输入拼进 SQL。

## 面试题

1. 为什么 engine 是全局的、只建一次，而 session 每个请求建一个？
2. `/health` 查数据库有什么意义？负载均衡器为什么关心它？
3. 数据库网络不通（丢包，而不是拒绝连接）时，`/health` 会卡多久？怎么处理？
