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
|<img src="https://user-images.githubusercontent.com/53690235/233387883-f05c0589-3f6e-4e6d-a3e9-ce31ac8deebc.png" width="50" height="50" />|<img src="https://user-images.githubusercontent.com/53690235/233387978-f454625b-6b12-449d-9f78-2efdbf6cf762.png" width="50" height="50" />|
|:---:|:---:|
|Python|Javascript|
## 프론트엔드
|<img src="https://user-images.githubusercontent.com/53690235/233388491-f21ba331-5dd9-41b6-9cf9-1da81ccc0f63.png" width="50" height="50" />|<img src="https://user-images.githubusercontent.com/53690235/233399068-02784351-26df-4724-b3af-b95c7a1a29fb.png" width="50" height="50" />|
|:---:|:---:|
|Bootstrap|Django|
## 백엔드
|<img src="https://user-images.githubusercontent.com/53690235/233393030-60cb263a-3a72-4307-8fd6-a99ffb43523b.png" width="50" height="50" />|
|:---:|
|Django|
## 데이터베이스
|<img src="https://user-images.githubusercontent.com/53690235/233382541-80335065-eddd-48f0-aef0-78865908f552.png" width="50" height="50" />|<img src="https://user-images.githubusercontent.com/53690235/233384512-ca8bc9ce-9546-4c82-8b5f-ce31d99a7146.png" width="50" height="50" />|
|:---:|
|SQLite|
## 형상관리 툴
|<img src="https://user-images.githubusercontent.com/53690235/233397733-4aebe3b5-2433-43ba-84a2-4aebb7bf0551.png" width="50" height="50" />|
|:---:|
|Git|
<br />
<br />

# 📚 DB 설계
![image](https://user-images.githubusercontent.com/53690235/233400752-4c89945a-0320-47ea-9d45-9fe88caa33e9.png)
<br />
<br />

# 💡 Issues
[InvalidOperationException: The model item passed into the ViewDataDictionary is of type '' ~](https://dong1936.tistory.com/34) <br />
[SqlException: Invalid object name 'APODModel' 오류 해결법](https://dong1936.tistory.com/35) <br />
[Development Mode 설정 오류 / Azure 배포과정](https://dong1936.tistory.com/37) <br />
[댓글 기능 구현](https://dong1936.tistory.com/46) <br />
[댓글 저장 방식에 대한 고찰](https://dong1936.tistory.com/47) <br />
[View와 RedirectToAction 메서드에 대한 고찰](https://dong1936.tistory.com/48) <br />
[여러날짜의 apod 정보를 가져와서 한번에 db에 저장하기 (feat. DB용량 안습)](https://dong1936.tistory.com/49) <br />
[img의 src 속성이 이미지가 아닌 비디오일 경우 iframe의 src 속성으로 비디오를 출력하는 기능 구현](https://dong1936.tistory.com/51) <br />
[게시 후와 게시 전의 DateTime.Now 값이 다른 문제](https://dong1936.tistory.com/52) <br />
<br />
<br />

# 🧑 개발 인원
혼자 개발하였습니다.
