@echo 1. Generate CA
openssl req -x509 -new -nodes -days 3650 -keyout ca.key -out ca.crt -subj "/CN=MyCA"

@echo 2. Generate Server Key/CSR/Cert
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=server"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

@echo 3. Generate Client Key/CSR/Cert
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=client"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365
