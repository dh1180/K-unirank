from flask import Flask, render_template
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'  # SQLite 사용 예시
db = SQLAlchemy(app)


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schoolname = db.Column(db.String(100), unique=True)
    score = db.Column(db.String(100))


# Flask 애플리케이션 컨텍스트 설정
with app.app_context():
    # 데이터베이스 생성
    db.create_all()

api_key = "dfac745a466d279dd3fcbc6c6dda4483"
url = "https://www.career.go.kr/cnet/openapi/getOpenApi?apiKey={}&svcType=api&svcCode=SCHOOL&contentType=json&gubun=univ_list&perPage=1000".format(
    api_key)
response = requests.get(url)
data = response.json()


@app.route("/")
def index():
    for item in data['dataSearch']['content']:
        new_school = School(schoolname=item['schoolName'], score=0)
        existing_school = School.query.filter_by(
            schoolname=item['schoolName']).first()
        if existing_school is None:
            db.session.add(new_school)
            db.session.commit()
        else:
            continue

    # 총 401개의 대학교가 있음
    schools = School.query.order_by(School.score.desc()).all()
    return render_template('index.html', schools=schools)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
