<script lang="ts">
  import { Eye, EyeOff } from 'lucide-svelte';
  import type { HTMLInputAttributes } from 'svelte/elements';

  export let id: string;
  export let name: string;
  export let autocomplete: HTMLInputAttributes['autocomplete'];
  export let label: string;
  export let minlength: number | undefined = undefined;
  export let required = false;
  export let disabled = false;

  let visible = false;
</script>

<label for={id}>
  {label}
  <span class="relative block">
    <input class="w-full pr-11" {id} {name} type={visible ? 'text' : 'password'} {autocomplete} {minlength} {required} {disabled} />
    <button class="password-toggle" type="button" onclick={() => (visible = !visible)} aria-label={visible ? `Sembunyikan ${label.toLowerCase()}` : `Tampilkan ${label.toLowerCase()}`} aria-pressed={visible} {disabled}>
      {#if visible}<EyeOff size={17} strokeWidth={1.8} aria-hidden="true" />{:else}<Eye size={17} strokeWidth={1.8} aria-hidden="true" />{/if}
    </button>
  </span>
</label>
