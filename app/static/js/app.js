const token={"Content-Type":"application/json","X-CSRFToken":window.CSRF_TOKEN};
function toBn(n){return String(n).replace(/[0-9]/g,d=>'০১২৩৪৫৬৭৮৯'[d])}
function formatQty(base,qty){
  qty=Number(qty);
  if(base==='piece')return toBn(qty)+' পিস যোগ হয়েছে';
  const big=base==='g'?'কেজি':'লিটার';
  const small=base==='g'?'গ্রাম':'মিলি';
  const whole=Math.floor(qty/1000);
  const remainder=qty%1000;
  if(whole>0&&remainder>0)return toBn(whole)+' '+big+' এবং '+toBn(remainder)+' '+small+' যোগ হয়েছে';
  if(whole>0)return toBn(whole)+' '+big+' যোগ হয়েছে';
  return toBn(remainder)+' '+small+' যোগ হয়েছে';
}
function unitLabel(base,qty){if(base==='piece')return qty===1?'পিস':qty+' পিস';if(qty==1000)return base==='g'?'কেজি':'লিটার';return qty+(base==='g'?' গ্রাম':' মিলি')}
function updatePrice(card){const unit=card.querySelector('.unit');if(!unit)return;const base=card.dataset.base,ppb=parseFloat(card.dataset.price),qty=Number(unit.value);const total=(ppb*qty).toFixed(2);card.querySelector('.price').textContent=total+' টাকা / '+unitLabel(base,qty)}
document.querySelectorAll('.unit').forEach(sel=>sel.addEventListener('change',()=>updatePrice(sel.closest('.product'))));
async function summary(){const r=await fetch('/bag/summary');const d=await r.json();document.querySelector('#cart-total').textContent=d.total+' টাকা'}
document.querySelectorAll('.add').forEach(button=>button.addEventListener('click',async()=>{const card=button.closest('.product'), unit=card.querySelector('.unit');const qty=unit?Number(unit.value):1;const r=await fetch('/bag',{method:'POST',headers:token,body:JSON.stringify({product_id:card.dataset.id,quantity_base:qty})});const d=await r.json();if(d.error){alert(d.error);return}document.querySelector('#cart-total').textContent=d.total+' টাকা';const out=card.querySelector('.feedback');out.textContent=formatQty(d.base_unit,d.product_qty);out.classList.remove('pop');void out.offsetWidth;out.classList.add('pop')}));summary();
const cart=document.querySelector('#floating-cart');let dx=0,dy=0,drag=false;cart.addEventListener('pointerdown',e=>{drag=true;dx=e.clientX-cart.getBoundingClientRect().left;dy=e.clientY-cart.getBoundingClientRect().top;cart.setPointerCapture(e.pointerId)});cart.addEventListener('pointermove',e=>{if(!drag)return;cart.style.left=Math.max(0,Math.min(innerWidth-cart.offsetWidth,e.clientX-dx))+'px';cart.style.top=Math.max(0,Math.min(innerHeight-cart.offsetHeight,e.clientY-dy))+'px';cart.style.right='auto';cart.style.bottom='auto'});cart.addEventListener('pointerup',()=>drag=false);
