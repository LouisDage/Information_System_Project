import os

#basedir = os.path.abspath(os.path.dirname(__file__))
#print("basedir: ", basedir)

class Config:
    TRACE = False
    TRACE_MAPPING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    TRACE_MAPPING = True
    SQLALCHEMY_ENGINE_ECHO = False
    SQLALCHEMY_DATABASE_URI = "postgresql://beergameadmin:beergameadminpass@localhost:5432/beergame"

class TestingConfig(Config):
    TESTING = True
    TRACE = True
    SQLALCHEMY_ENGINE_ECHO = False
    SQLALCHEMY_DATABASE_URI = "postgresql://beergameadmin:beergameadminpass@localhost:5432/beergame-test"
    #TRACE_MAPPING = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    # 'production': ProductionConfig,
    # 'heroku': HerokuConfig,
    # 'docker': DockerConfig,
    # 'unix': UnixConfig,
    'default': DevelopmentConfig
}
