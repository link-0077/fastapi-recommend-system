from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
#数据库配置（MySQL）
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME} "
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#数据库模型定义
# 用户表
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))

# 物品表（商品/文章）
class DBItem(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(String(255))

# 用户行为表：记录用户浏览了哪些物品
class DBUserBehavior(Base):
    __tablename__ = "user_behavior"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))

Base.metadata.create_all(bind=engine)

#FastAPI实例
app = FastAPI(title="简易推荐系统API", description="RESTful推荐后端")

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Pydantic 请求模型
class UserCreate(BaseModel):
    username: str

class ItemCreate(BaseModel):
    name: str
    description: str

class BehaviorCreate(BaseModel):
    user_id: int
    item_id: int

#RESTful 接口
# 1. 创建用户
@app.post("/users", summary="新建用户")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = DBUser(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 2. 创建物品
@app.post("/items", summary="新建物品")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = DBItem(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# 3. 记录用户浏览行为
@app.post("/behavior", summary="记录用户浏览物品")
def add_behavior(behavior: BehaviorCreate, db: Session = Depends(get_db)):
    # 校验用户、物品是否存在
    user = db.query(DBUser).get(behavior.user_id)
    item = db.query(DBItem).get(behavior.item_id)
    if not user or not item:
        raise HTTPException(status_code=404, detail="用户或物品不存在")
    db_behavior = DBUserBehavior(user_id=behavior.user_id, item_id=behavior.item_id)
    db.add(db_behavior)
    db.commit()
    db.refresh(db_behavior)
    return {"msg": "行为记录成功", "data": db_behavior}

# 4. 核心接口：给用户做物品推荐（简易协同过滤）
@app.get("/recommend/{user_id}", summary="获取用户推荐列表")
def get_recommend(user_id: int, db: Session = Depends(get_db)):
    # 1 获取当前用户浏览过的所有物品ID
    user_viewed_items = db.query(DBUserBehavior.item_id).filter(DBUserBehavior.user_id == user_id).all()
    viewed_ids = [x[0] for x in user_viewed_items]
    if not viewed_ids:
        return {"msg": "暂无浏览行为，无法推荐", "recommend_items": []}

    # 2 找到和当前用户看过相同物品的其他用户
    similar_user_ids = db.query(DBUserBehavior.user_id).filter(DBUserBehavior.item_id.in_(viewed_ids)).distinct().all()
    similar_user_ids = [x[0] for x in similar_user_ids if x[0] != user_id]
    if not similar_user_ids:
        return {"msg": "未找到相似用户", "recommend_items": []}

    # 3 获取相似用户看过，但当前用户没看过的物品作为推荐
    recommend_item_ids = db.query(DBUserBehavior.item_id)\
        .filter(DBUserBehavior.user_id.in_(similar_user_ids))\
        .filter(DBUserBehavior.item_id.not_in(viewed_ids))\
        .distinct().limit(5).all()
    recommend_item_ids = [x[0] for x in recommend_item_ids]

    # 查询物品详情
    recommend_items = db.query(DBItem).filter(DBItem.id.in_(recommend_item_ids)).all()
    return {"user_id": user_id, "recommend_items": recommend_items}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
