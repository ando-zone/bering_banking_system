# bering_banking_system

## 간략한 소개 및 주요 기능
---

온라인 은행 시스템을 모방하여, 사용자가 계정을 생성하고 본인의 계좌를 생성할 수 있으며, 계좌에 등록한 카드를 이용하여 입출금 및 계좌 잔액 확인을 할 수 있는 API 서비스입니다. 주요 기능은 다음과 같습니다.

1. Create user account
2. Register cards(plural!)
3. Disable card
4. Enable card
5. Check account balance
6. Withdraw cash
7. Deposit cash

## 기술 스택
---

- Flask
- RDBMS (SQLite)

## 회고
---

- 위에서 열거한 주요 기능 작성을 충실히 구현하는 것에 초점을 맞추어 해당 API 서비스를 구축했으며, 주요 기능에 대한 test 작성도 pytest를 이용하여 모두 마쳤습니다. 비동기로 테스트를 진행하여 서비스의 성능을 높이려고 했으나, 아직은 해당 방식으로 테스트 진행이 익숙하지 않아 동기 테스트로 작업을 전환하여 마무리했습니다. (tests/unit 디렉토리 내 테스트 코드 참조)
- 상태 패턴을 적용하여 Card’s state 변화에 따라 카드 객체로 할 수 있는 행위(인출 및 입금)가 제한되거나 허용되도록 구현하였습니다. (app/card_state.py, app/models.py 참조)
- 가능한 모든 메서드에 logging을 적용하고 상황에 맞게 적절한 logging level을 부여함으로써 사용자의 행동을 추적할 수 있도록 하였습니다.
- 프로젝트의 규모를 고려하여 익숙하지만 무거운 django프레임워크 대신 가벼운 flask 프레임워크를 선택해 작업을 진행했습니다. 이전 dev_meme_test 프로젝트에서도 flask 프레임워크를 사용했었지만 보다 다양하고 복잡한 기능들을 구현하며 플라스크 프레임워크에 대한 많은 경험을 할 수 있었고, 서로 다른 두 프레임워크에 대한 이해도도 높일 수 있는 좋은 기회였습니다.

## ERD 다이어그램으로 모델 구조 한 눈에 보기
---
![bering_banking_system_ERD](https://github.com/ando-zone/bering_banking_system/assets/119149274/5d0ec1d0-84ad-45bb-a390-1a270fd6c5ac)

