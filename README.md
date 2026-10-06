# FastAPI简易物品推荐系统
## 项目简介
本项目是基于Python+FastAPI开发的轻量后端推荐服务，独立完成开发。实现RESTful风格API，记录用户物品浏览行为，使用协同过滤思想做个性化物品推荐。可本地启动，自带交互式接口文档，用于后端技术学习与实践。

## 技术栈
- 编程语言：Python3
- Web框架：FastAPI
- 数据库：MySQL
- ORM框架：SQLAlchemy
- API规范：RESTful

## 功能清单
1. 用户管理：创建用户
2. 物品管理：创建物品
3. 行为埋点：记录用户浏览物品的行为数据
4. 个性化推荐：基于用户浏览行为，使用协同过滤算法，推荐相似用户浏览过的物品

## 环境准备
### 1. 安装依赖
```bash
pip install fastapi uvicorn sqlalchemy pymysql
