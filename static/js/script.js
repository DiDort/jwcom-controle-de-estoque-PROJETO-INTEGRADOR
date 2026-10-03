function toast(msg){let t=document.getElementById('toast');t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',2500)}
function closeModals(){document.querySelectorAll('.modal.open').forEach(m=>m.classList.remove('open'))}
document.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.open).classList.add('open'));
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=closeModals);
document.querySelectorAll('[data-menu]').forEach(b=>b.onclick=e=>{e.stopPropagation();document.querySelectorAll('.row-menu.open').forEach(x=>x.classList.remove('open'));b.nextElementSibling.classList.toggle('open')});
document.addEventListener('click',()=>document.querySelectorAll('.row-menu.open').forEach(x=>x.classList.remove('open')));
let pendingRow=null;
document.querySelectorAll('[data-deactivate]').forEach(b=>b.onclick=e=>{e.stopPropagation();pendingRow=b.closest('tr');document.getElementById('confirmModal').classList.add('open')});
document.getElementById('confirmDeactivate')?.addEventListener('click',()=>{if(pendingRow){pendingRow.dataset.status='inativos';pendingRow.style.display='none';pendingRow.querySelector('.badge').className='badge neutral';pendingRow.querySelector('.badge').textContent='Inativo'}closeModals();toast('Produto inativado no protótipo. O histórico foi preservado.')});
document.querySelectorAll('[data-reactivate]').forEach(b=>b.onclick=()=>toast('Produto reativado no protótipo.'));
function filterTable(inputId,tableId){let i=document.getElementById(inputId),t=document.getElementById(tableId);if(i&&t)i.oninput=()=>[...t.tBodies[0].rows].forEach(r=>r.style.display=r.innerText.toLowerCase().includes(i.value.toLowerCase())?'':'none')}
filterTable('productSearch','productsTable');filterTable('historySearch','historyTable');
document.getElementById('statusFilter')?.addEventListener('change',e=>{let v=e.target.value;document.querySelectorAll('#productsTable tbody tr').forEach(r=>r.style.display=(v==='todos'||r.dataset.status===v)?'':'none')});
document.querySelectorAll('input[name="tipo"]').forEach(r=>r.addEventListener('change',()=>{let t=document.querySelector('input[name="tipo"]:checked').value;document.getElementById('channelField').classList.toggle('hidden',t!=='saida');document.getElementById('reasonField').classList.toggle('hidden',t!=='ajuste');document.getElementById('quantityLabel').textContent=t==='ajuste'?'Quantidade física encontrada':'Quantidade'}));
document.getElementById('exportProducts')?.addEventListener('click',()=>{toast('Na versão final, este botão gerará o PDF com SKU, nome, quantidade e última movimentação.')});
document.querySelectorAll('[data-edit]').forEach(b=>b.addEventListener('click',()=>{
  document.getElementById('editSku').value=b.dataset.sku;
  document.getElementById('editNome').value=b.dataset.nome;
  document.getElementById('editMin').value=b.dataset.min;
  document.getElementById('editForm').action='/produtos/'+b.dataset.id+'/editar';
  document.getElementById('editModal').classList.add('open');
}));
