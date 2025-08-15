
(async function(){
  const $q = s => document.querySelector(s);
  const $results = $q('#results');
  const $search = $q('#search');
  const $fda = $q('#filter-fda');
  const $ema = $q('#filter-ema');
  const $today = $q('#filter-today');
  const $tpl = $q('#card-tpl');
  const $last = $q('#last-updated');

  async function load(){
    try{
      const res = await fetch('./data/latest.json', {cache: 'no-store'});
      const data = await res.json();
      $last.textContent = `마지막 업데이트: ${data.generated_at} (총 ${data.items.length}건)`;
      state.items = data.items.map(x => ({...x, _t:new Date(x.published)}));
      render();
    }catch(e){
      console.error(e);
      $results.innerHTML = '<p>데이터를 불러오지 못했습니다. 저장소에 latest.json이 있는지 확인하세요.</p>';
    }
  }

  const state = { items: [] };

  function render(){
    const q = ($search.value || '').trim();
    const todayOn = $today.checked;
    const now = new Date(); 
    const ymd = now.toISOString().slice(0,10);
    const showFDA = $fda.checked, showEMA = $ema.checked;

    const list = state.items.filter(it => {
      if (todayOn && it.published.slice(0,10) !== ymd) return false;
      if (!showFDA && it.label === 'FDA') return false;
      if (!showEMA && it.label === 'EMA') return false;
      if (!q) return true;
      const hay = (it.title + ' ' + (it.summary || '') + ' ' + (it.source || '')).toLowerCase();
      return hay.includes(q.toLowerCase());
    }).sort((a,b) => b._t - a._t);

    $results.innerHTML = '';
    for(const it of list){
      const node = $tpl.content.cloneNode(true);
      const $badge = node.querySelector('.badge');
      const $title = node.querySelector('.title');
      const $meta = node.querySelector('.meta');
      const $source = node.querySelector('.source');
      $badge.textContent = it.label;
      $badge.classList.toggle('EMA', it.label === 'EMA');
      $title.textContent = it.title;
      $title.href = it.link;
      const dt = new Date(it.published);
      $meta.textContent = `${dt.toLocaleString()} · ${new URL(it.link).hostname}`;
      $source.textContent = it.source || '';
      $results.appendChild(node);
    }

    if(list.length === 0){
      $results.innerHTML = '<p>조건에 맞는 결과가 없습니다.</p>';
    }
  }

  $search.addEventListener('input', render);
  [$fda,$ema,$today].forEach(el => el.addEventListener('change', render));

  load();
})();
