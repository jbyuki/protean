var canvas = document.createElement('canvas');
canvas.id = 'canvas';

document.body.appendChild(canvas);

canvas.width = 640;
canvas.height = 480;

ctx = canvas.getContext('2d');
console.log(ctx);

ctx.fillStyle = "rgb(200 0 0)";
ctx.fillRect(0, 0, 640, 480);


