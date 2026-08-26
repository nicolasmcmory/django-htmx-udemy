document.addEventListener('alpine:init', () => {
  Alpine.data('timedVisibility', (initialShow = true) => ({
    show: initialShow,

    init() {
      if (!this.show) return;

      window.setTimeout(() => {
        this.show = false;
      }, 2000);
    },
  }));

  Alpine.data('confirmModal', () => ({
    open: false,
    question: '',
    pendingEvent: null,

    init() {
      // Htmx 4's confirm event is now cancellable, so we can prevent the default behavior and show our own modal instead
      document.body.addEventListener('htmx:confirm', (event) => {
        const question = event.detail.ctx?.confirm;
        if (!question) return;

        // Prevent the default behavior of htmx's confirm event, which would normally show a browser confirmation dialog
        event.preventDefault();
        this.question = question;
        this.pendingEvent = event;
        this.open = true;
      });
    },

    confirm() {
      const event = this.pendingEvent;
      this.reset();

      // htmx 4's issueRequest takes no arguments (no skipConfirmation flag)
      if (event) event.detail.issueRequest();
    },

    close() {
      const event = this.pendingEvent;
      this.reset();

      // dropRequest explicitly cancels the deferred request (htmx 4 API)
      if (event) event.detail.dropRequest();
    },

    reset() {
      this.open = false;
      this.question = '';
      this.pendingEvent = null;
    },
  }));
});
