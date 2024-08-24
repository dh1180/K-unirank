# 🗳️ K-unirank
자신이 생각하는 순위에 대학교를 투표하여 사람들이 생각하는 보편적인 대학순위를 알 수 있는 웹사이트입니다.
APOD api가 갱신될 때마다 APOD 정보(우주의 사진 및 사진에 대한 제목, 날짜, 설명 등)를 블로그 형식으로 자동 업로드하는 웹사이트입니다.
* 각 대학교는 하나의 순위에 투표할 수 있습니다.
* 동일한 순위라고 생각하는 대학교들이 있을 수 있어 하나의 순위에 여러 대학교를 투표할 수 있습니다(1:N).
* 자신이 투표한 대학교의 순위는 언제든 취소할 수 있습니다.
* 각 대학교의 테이블을 클릭하면 해당 대학교의 정시, 수시등급을 볼 수 있습니다.

https://www.k-unirank.com/
<br />

# 🗃 왜 만들었나요?
현재 고등학생들이 대학교를 지원할 때 고려하는 요소 중의 하나가 대학교의 순위입니다. <br />
각종 커뮤니티 사이트에서 다양한 자료를 이용해 대학교의 순위를 매기고 있지만 이 또한 개인의 주관이 반영된 부정확한 자료일 가능성이 커 해당 대학교 순위에 동의하지 않는 사람들이 많습니다. <br />
따라서 모두가 대학교의 순위를 결정할 수 있는 사이트를 개발하여 아무도 불평을 할 수 없는 보편적인 대학교의 순위를 만들고 싶어 K-unirank라는 웹을 개발하게 되었습니다.
<br />
<br />

# 📅 개발 기간
2024-03-01 ~ 2024-08-24 (배포 후 중간중간 수정한 것까지 포함하였습니다.)
<br />
<br />

# 💻 기술 스택
## 개발 언어
|<img src="https://github.com/user-attachments/assets/8a24a293-a03b-43a7-9f48-61ec94a0b1f7" width="50" height="50" />|<img src="https://user-images.githubusercontent.com/53690235/233387978-f454625b-6b12-449d-9f78-2efdbf6cf762.png" width="50" height="50" />|
|:---:|:---:|
|Python|Javascript|
## 프론트엔드
|<img src="https://user-images.githubusercontent.com/53690235/233388491-f21ba331-5dd9-41b6-9cf9-1da81ccc0f63.png" width="50" height="50" />|<img src="https://github.com/user-attachments/assets/999df902-5abb-4eab-9cd5-f674afbb45fc" width="50" height="50" />|
|:---:|:---:|
|Bootstrap|Django|
## 백엔드
|<img src="https://github.com/user-attachments/assets/999df902-5abb-4eab-9cd5-f674afbb45fc" width="50" height="50" />|
|:---:|
|Django|
## 데이터베이스
|<img src="https://github.com/user-attachments/assets/514df0fa-12c3-4584-9daf-e120d5beb46e" width="85" height="50" />|
|:---:|
|SQLite|
## 형상관리 툴
|<img src="https://user-images.githubusercontent.com/53690235/233397733-4aebe3b5-2433-43ba-84a2-4aebb7bf0551.png" width="50" height="50" />|
|:---:|
|Git|
<br />
<br />

# 📚 DB 설계
![K-unirank](https://github.com/user-attachments/assets/6b5f1f26-f106-4159-b3c3-47df422e2210)
<br />
<br />

# 사이트 기능
### 1. 메인 페이지
<img src="https://github.com/user-attachments/assets/90d5d265-04df-49ce-9906-9a030e2f5565" width="500">
<img src="https://github.com/user-attachments/assets/222f123b-fd13-4ccd-91fa-44a905ffd8b5" width="500">

* 대학교 클릭 시 모달창이 생성되면서 해당 학교의 수시, 정시 등급을 볼 수 있습니다.
* 로그인 시 투표한 학교 옆에 체크 표시가 나타나고 투표하지 않은 학교 옆에는 X 표시가 나타납니다.
* 또한 상단 내비게이션 바에 대학교를 투표할 수 있는 버튼과 투표한 학교를 볼 수 있는 버튼이 나타납니다.

### 2. 대학 순위 투표 페이지

# 💡 Issues
[[Flask/K-unirank] flask-uploads 라이브러리에 대하여](https://dong1936.tistory.com/61) <br />
[[Django/K-unirank] django-allauth signup 페이지 없애는 법](https://dong1936.tistory.com/62) <br />
[[Django/K-unirank] User 모델에 필드를 추가하는 깔@롱 쌈@뽕한 법 (feat. 추가한 필드를 admin 페이지에서 확인하는 법)](https://dong1936.tistory.com/63) <br />
[[Django/K-unirank] javascript click 이벤트를 구현하는 두가지 방법](https://dong1936.tistory.com/64) <br />
[[Django/K-unirank] 사람들이 서비스 이용을 하지 않는다..](https://dong1936.tistory.com/65) <br />
[[Django/K-unirank] 이용자 수 1.2천명 달성!](https://dong1936.tistory.com/66) <br />
[[Django/K-unirank] HTML 파비콘이 상단 메뉴바에는 적용 되는데 구글 검색결과에는 적용이 안되는 건에 대하여](https://dong1936.tistory.com/67) <br />
[[Django/K-unirank] .gitignore를 작성했는데 .gitignore 파일에 적힌 폴더와 파일이 레포지터리에 남아있는 현상](https://dong1936.tistory.com/68) <br />
<br />
<br />

# 🧑 개발 인원
혼자 개발하였습니다.
