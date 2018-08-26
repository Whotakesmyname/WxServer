# WxServer  
## Deprecation
本仓库已许久不再使用，留存仅作纪念。  
本仓库的复杂构造源于微信公众号对个人账户功能的严重限制，因此采用了诸多Workarounds实现功能，逻辑也十分的绕人。小程序出现并允许个人用户开发后逻辑代码早已全部重写，并分离了前后端，效果美观代码清晰。虽然随着个人毕业，之前的服务器到期，该小程序也已停止运行；也因为本地Tensorflow验证码识别资源开销等问题，暂时没有重新运行的计划。  

但其中的教务API模块之后又做过整理与重构，并进行开源。若感兴趣请见Repo[BFSUjwc](https://github.com/Whotakesmyname/BFSUjwc)，但不包含服务器代码。谢谢。

---------------
## Old Content
 重写了教务系统爬取到的接口API，并简化逻辑集成到一个文件中，提升了代码的可读性及易用性。  
 重写了多项工具，并提取到了utils.py中。  
 原有web.py驱动的，以微信公众号官方API为基础的服务器程序线程安全无法明确。本项目重写于模块itchat之上，基于微信web版爬取到的API提供服务。  
 采用主仆模式的多线程结构，增强了并发请求处理能力及容错能力。actions.py 中除'Login'类（待日后优化）及'QueryManager'类（管理连接池用，无需优化）以外，其他均可按需灵活增发线程以增强处理能力。  
 
A server offering academic affair supports on Wechat, based on itchat.  
This is a multithreading version server in order to handle large amounts of concurrent requests, so besides 'Login' class and 'PoolManager' class, other actions have been thread safe.  

The old server on SAE, based on Wechat MP API is abandoned.  

The BFSU academic affair website's API has been rewritten and optimized. You can find it in bfsujwc.py.  

itchat is an amazing module saving me a lot of time.  
