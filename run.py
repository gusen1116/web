from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 데이터베이스 및 로그인 관리자 초기화
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

# Flask 앱 생성
app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')

# 기본 설정
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 확장 모듈 초기화
db.init_app(app)
login_manager.init_app(app)
socketio.init_app(app)

# 라우트 블루프린트 설정
from flask import Blueprint, render_template

# 메인 블루프린트
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

# 블로그 블루프린트
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

@blog_bp.route('/')
def index():
    return render_template('blog/index.html')

@blog_bp.route('/post/<int:post_id>')
def post(post_id):
    return render_template('blog/post.html', post_id=post_id)

# 인증 블루프린트
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
def login():
    return render_template('auth/login.html')

@auth_bp.route('/register')
def register():
    return render_template('auth/register.html')

# 시뮬레이션 블루프린트
simulation_bp = Blueprint('simulation', __name__, url_prefix='/simulation')

@simulation_bp.route('/')
def index():
    return render_template('simulation/index.html')

# 블루프린트 등록
app.register_blueprint(main_bp)
app.register_blueprint(blog_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(simulation_bp)

# 로그인 관리자 설정
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    # 임시 더미 함수
    return None

# 앱 실행
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)