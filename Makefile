local:
	heroku local

deploy:
	heroku container:push web

setup:
	heroku apps:create tesstvgapp
