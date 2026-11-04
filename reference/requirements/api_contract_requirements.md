# API Contract Requirements
GET /customers/{id}
GET /complaints/{id}
GET /customers/{id}/complaints
POST /complaints → 201
PATCH /complaints/{id}/status
Missing → 404; invalid body → 422; invalid status transition → stable conflict/validation error.
