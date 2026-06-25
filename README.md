# Chase Setup

- Create virtual environment, python version 3.9.0

  ```bash
  pyenv local 3.9.0
  python -m venv venv
  ```

- Activate the virtual environment

  ```bash
  [Linux/ Mac]
  source venv/bin/activate

  [Windows]
  venv\Scripts\activate
  ```

- Upgrade the PIP

  ```bash
  pip install --upgrade pip
  ```

  or

  ```bash
  python -m pip install --upgrade pip
  ```

- Install the Django Packages

  ```bash
  pip install -r requirements.txt
  ```

    <!-- setting-chase.dev.env -->

- Copy `setting-chase.dev.env.sample`, then rename to `setting-chase.dev.env`, and edit the your own email and password

  ```bash
  LOCAL_ADMIN_USERNAME=myemail@codetinker.com
  LOCAL_ADMIN_PASSWORD=mypassword
  ```

- Run initial migration

  ```bash
  python manage.py migrate
  ```

- Create SuperAdmin

  ```bash
  python manage.py update_core --setup
  ```

# Run the server

- Run update_core (when necessary)

  ```bash
  python manage.py update_core
  ```

- Run migration (when necessary)

  ```bash
  python manage.py migrate
  ```

- Run server

  ```bash
  python manage.py runserver_plus
  ```
