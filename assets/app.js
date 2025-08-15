(async function(){
  const $q = s => document.querySelector(s);
  const $results = $q('#results');
  const $search = $q('#search');
  const $fda = $q('#filter-fda');
  const $ema = $q('#filter-ema');
  const $today = $q('#filter-today');
  const $tpl = $q('#card-tpl');
  const $last = $q('#last-updated');

  // KST YYYY-MM-DD
  const kstYmd = () => {
    const fmt = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit' });
    return fmt.format(new Date()); // e.g. "2025-08-15"
  };

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
    const q = ($search.value || '').trim().toLowerCase();
    const showFDA = $fda.checked, showEMA = $ema.checked;
    const kst = kstYmd();

    const list = state.items.filter(it => {
      if ($today.checked) {
        // published의 앞 10자리만 비교 (KST로 저장되어 있음)
        if ((it.published || '').slice(0,10) !== kst) return false;
      }
      if (!showFDA && it.label === 'FDA') return false;
      if (!showEMA && it.label === 'EMA') return false;
      if (!q) return true;
      const hay = (it.title + ' ' + (it.summary || '') + ' ' + (it.source || '')).toLowerCase();
      return hay.includes(q);
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
      $meta.textContent = `${dt.toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })} · ${new URL(it.link).hostname}`;
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
