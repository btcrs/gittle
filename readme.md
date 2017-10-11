Gittle
------
> Tiny Git

Usage
----- 


```
pip install -r requirements.txt
python manage.py runserver

```

Examples
--------

Creating  repo:

```
 curl -X POST \
  {{api}}/{{user}}/{{project}}/create \
  -H "Content-Type: application/json"
```
