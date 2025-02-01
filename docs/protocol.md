Command
=======

```
{
	"cmd" :  string,
	"data" : object
}
```

`execute`
---------

> client -> server

* `cmd` : `"execute"`
* `data` :

```
{
	"name": string,
	"lines" : [string]
}
```

Notes:

* `name`: section name
* `lines`: list of lines of literate style code

`output`
---------

> server -> client

* `cmd` : `"output"`
* `data` :

```
{
	"task_id": int,
	"text" : string
}
```

`notify`
---------

> server -> client

* `cmd` : `"notify"`
* `data` :

```
{
	"status": string,
	"section" : string?
}
```

Notes:

* `status`: Can be one of `idle`, `running`
* `section`: If `running`, specifies the section name
