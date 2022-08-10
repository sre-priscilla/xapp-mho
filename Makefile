env-image:
	docker build -t 192.168.1.5:5000/xapp-mho:env --target env .

app-image:
	docker build -t 192.168.1.5:5000/xapp-mho:dev .

push:
	docker push 192.168.1.5:5000/xapp-mho:dev

update:
	kubectl delete pod -n sdran -l app=xapp-demo

install:
	kubectl apply -f manifests/deploy.yaml

uninstall:
	kubectl delete -f manifests/deploy.yaml

secret:
	kubectl create secret generic xapp-mho -n sdran --from-file pki/ca.crt --from-file pki/tls.crt --from-file pki/tls.key