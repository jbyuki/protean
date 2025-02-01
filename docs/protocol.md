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
