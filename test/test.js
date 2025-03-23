const sleep = msec => new Promise(resolve => setTimeout(resolve, msec));

console.log('hi');
await sleep(1000);
console.log('end');

