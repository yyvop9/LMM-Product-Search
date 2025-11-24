Modify API Documentation v1.0

1. 텍스트 검색 (Text Search)

사용자가 입력한 키워드를 영어로 번역한 후, 유사한 스타일의 제품을 검색합니다.

Endpoint: POST /search/text

Description: 한글 쿼리 지원 (자동 번역)

Request Body

{
  "query": "파란색 셔츠",
  "top_k": 5
}


Response (200 OK)

[
  {
    "id": "9378.jpg",
    "product_name": "Blue Oxford Shirt",
    "description": "Classic fit...",
    "brand": "Polo",
    "color": "Blue",
    "size": "M, L",
    "price": 89000,
    "season": "봄, 가을",
    "image_file": "9378.jpg"
  },
  ...
]


2. 스마트 검색 (Smart Search - AI Agent)

자연어 질문을 LLM(Watsonx)이 분석하여 최적의 검색 키워드와 필터(계절 등)를 생성해 검색합니다.

Endpoint: POST /search/smart

Description: 문맥(Context) 이해 및 추천

Request Body

{
  "query": "크리스마스 데이트룩 추천해줘",
  "top_k": 5
}


Response (200 OK)

(응답 형식은 텍스트 검색과 동일합니다.)

3. 이미지 검색 (Image Search)

사용자가 업로드한 이미지와 시각적으로 가장 유사한 제품을 검색합니다.

Endpoint: POST /search/image

Content-Type: multipart/form-data

Request Body (Form Data)

Key

Type

Description

file

File

업로드할 이미지 파일 (.jpg, .png)

top_k

Integer

(Optional) 반환 개수 (기본 5)

Response (200 OK)

(응답 형식은 텍스트 검색과 동일합니다.)

4. 연관 상품 추천 (Related Items)

특정 상품과 스타일이 유사한 다른 상품들을 추천합니다. (자기 자신 제외)

Endpoint: GET /search/related/{item_id}

Example: /search/related/9378.jpg?top_k=5

Response (200 OK)

(응답 형식은 텍스트 검색과 동일합니다.)

5. 상품 상세 정보 (Product Detail)

특정 상품의 모든 메타데이터(가격, 브랜드, 계절 등)를 조회합니다.

Endpoint: GET /product/{item_id}

Example: /product/9378.jpg

Response (200 OK)

{
  "id": "9378.jpg",
  "product_name": "Blue Oxford Shirt",
  "description": "Classic fit...",
  "brand": "Polo",
  "color": "Blue",
  "size": "M, L",
  "price": 89000,
  "season": "봄, 가을",
  "image_file": "9378.jpg"
}


6. 관리자 로그 조회 (Admin Logs)

사용자들의 검색 기록(쿼리, 타입, 시간)을 최신순으로 조회합니다.

Endpoint: GET /admin/logs

Response (200 OK)

[
  {
    "id": 101,
    "search_type": "text",
    "query": "겨울 코트",
    "filename": null,
    "created_at": "2025-11-24T10:00:00"
  },
  {
    "id": 102,
    "search_type": "image",
    "query": null,
    "filename": "my_style.jpg",
    "created_at": "2025-11-24T10:05:00"
  }
]
