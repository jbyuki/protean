# ntpy

`ntpy` is a server which runs literate python designed for the experimentation of realtime applications.  

**work-in-progress**

Status:

- [x] Execute
- [ ] Interrupt kernel
- [ ] Restart kernel
- [ ] Multiple kernels
- [x] browser frontend
- [x] error display in frontend
- [x] redirect stdout to frontend
- [x] display latex in frontend
- [x] redirect plots to frontend

Motivation
----------

<details>

Code experimentation with tools such as Jupyter notebook has proved its usefulness in everyday programming many times that I'm fully convinced by it for quick and dirty experimentation. It provides sort of a middle ground between, on one end, the simple REPL and on the other end, the .py script file. It still keeps all its state like the REPL but also provides the means to write relatively complex code in a single cell. State keeping is critical for experimentation as it provides a way to endlessly manipulate the data until we are satisfied without the need to rerun the entire process everytime. However one critcally lacking feature in my opinion is the ability to experiment with realtime applications. Realtime application by principle, usually contain a main loop which needs to run endlessly. Obviously running directly a endless loop in a cell is a bad idea. There are ways to workaround this such as running the loop in a separate thread and display the realtime application in a widget for instance, if possible. However this adds a heavy abstraction layer which hinders direct manipulation of the said realtime application.

The main idea of `ntpy` is to instead run literate python code. For example, the code block for a main loop (written using the v2 ntangle syntax as explained [here](https://github.com/jbyuki/ntangle.nvim/blob/master/doc/ntangle.txt)):

```py
;; main loop
while True:
	; read io
	; process
	; show
	ntpy.sleep()
```

In a first phase the code block for the main loop is sent, subsequently, the user could define the `read io` section and send the corresponding code:

```py
;; read io
x,y,z = sensor.read()
```

The `read io` reference in the `main loop` section would now point to the newly added `read io` section and execute it on its next iteration, thus effectively modifying the realtime code while its running. This shows the basic principle behind `ntpy`.

</details>

Clients
-------

* [ntpy.nvim](https://github.com/jbyuki/ntpy.nvim) - Neovim client for ntpy
