from app.adapters.db.sqlalchemy_user_repository import SqlAlchemyUserRepository

def test_create_and_get_user(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    u = repo.create("Rahul","T","testrepo@example.com","testpw@repo123")
    assert u.id is not None
    got = repo.get_by_email("testrepo@example.com")
    assert got and got.id == u.id
