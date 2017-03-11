# WxServer
 重写了教务系统爬取到的接口API，并简化逻辑集成到一个文件中，提升了代码的可读性及易用性。
 重写了多项工具，并提取到了utils.py中。
 原有web.py驱动的，以微信公众号官方API为基础的服务器程序线程安全无法明确。本项目重写于模块itchat之上，基于微信web版爬取到的API提供服务。
 采用主仆模式的多线程结构，增强了并发请求处理能力及容错能力。actions.py 中除'Login'类（待日后优化）及'QueryManager'类（管理连接池用，无需优化）以外，其他均可按需灵活增发线程以增强处理能力。
 
A server offering academic affair supports on Wechat, based on itchat.
This is a multithreading version server in order to handle large amounts of concurrent requests, so besides 'Login' class and 'PoolManager' class, other actions have been thread safe.

The old server on SAE, based on Wechat MP API is abandoned.

The BFSU academic affair website's API has been rewritten and optimized. You can find it in bfsujwc.py.

itchat is an amazing module saving me a lot of time.
