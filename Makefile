image:
	nerdctl -n k8s.io build -t xapp-mho:dev .

update:
	kubectl delete pod -n sdran -l app=xapp-demo

install:
	kubectl apply -f deploy.yaml

uninstall:
	kubectl delete -f deploy.yaml

secret:
	kubectl create secret generic xapp-mho -n sdran --from-file pki/ca.crt --from-file pki/tls.crt --from-file pki/tls.key