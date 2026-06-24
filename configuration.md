## Basic setup
1. Step 1
- Copy `setting-chase.dev.env.sample`, then rename to `setting-chase.dev.env`, and edit the your own email and password

  ```bash
  LOCAL_ADMIN_USERNAME=myemail@codetinker.com
  LOCAL_ADMIN_PASSWORD=mypassword
  ```


2. Step 2
- follow `README.md`

## Run server
```bash
python manage.py runserver_plus
```

## To create dummy data
```bash
python manage.py create_data
```