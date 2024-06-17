const telInputs = document.querySelectorAll('.tel');

telInputs.forEach(inp => {
  inp.addEventListener('focus', _ => {
    if (!/^\+7$/.test(inp.value)) {
      inp.value = new String(inp.value).length >= 2 ? inp.value : '+7';
    }
  });

  inp.addEventListener('input', _ => {
    if (inp.value.length < 2 || !inp.value.startsWith('+7')) {
      inp.value = '+7';
    } else if (inp.value.length > 12) {
      inp.value = inp.value.slice(0, 12);
    }
  });

  inp.addEventListener('keypress', e => {
    if (!/\d/.test(e.key) && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
    }
  });

  inp.addEventListener('keydown', e => {
    if (e.key === 'Backspace' && inp.selectionStart <= 2) {
      e.preventDefault();
    }
  });
});