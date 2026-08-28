<script lang="ts">
  import { enhance } from '$app/forms';
  import type { SubmitFunction } from '@sveltejs/kit';
  import {
    BrainCircuit,
    Gauge,
    LogOut,
    ScanLine,
    ScrollText,
    X
  } from 'lucide-svelte';

  export let title: string;
  export let eyebrow = 'Web Admin SapiKenal';
  export let active = '';
  export let user: App.Locals['user'];

  const links = [
    { href: '/dashboard', label: 'Dashboard', icon: Gauge },
    { href: '/predictions', label: 'Prediksi', icon: ScanLine },
    { href: '/models', label: 'Model AI', icon: BrainCircuit },
    { href: '/audit-logs', label: 'Audit log', icon: ScrollText }
  ];

  let logoutDialog: HTMLDialogElement | undefined;
  let isLoggingOut = false;
  const enhanceLogout: SubmitFunction = () => {
    isLoggingOut = true;
    return async ({ update }) => {
      await update();
      isLoggingOut = false;
    };
  };
</script>

<div class="grid min-h-dvh grid-cols-1 bg-[#f6f8f7] text-[#17241f] lg:grid-cols-[16.5rem_minmax(0,1fr)]">
  <aside class="flex h-auto flex-col border-b border-[#e3e9e5] bg-[#fbfcfb] p-4 lg:sticky lg:top-0 lg:h-dvh lg:border-b-0 lg:border-r">
    <a class="mx-1 mb-4 flex items-center gap-3 text-inherit no-underline lg:mb-8" href="/dashboard" aria-label="SapiKenal Admin">
      <img class="size-[2.35rem] shrink-0 rounded-[.7rem] object-cover shadow-[0_5px_14px_rgba(23,107,73,.16)]" src="/logo.png" alt="Logo SapiKenal" />
      <span class="grid min-w-0 gap-0.5"><strong class="text-[.92rem] tracking-[-.01em]">SapiKenal</strong><small class="truncate text-[.72rem] text-[#708078]">Admin Console</small></span>
    </a>

    <div class="mx-2.5 mb-2 hidden text-[.65rem] font-bold uppercase tracking-[.11em] text-[#88958e] lg:block">Workspace</div>
    <nav class="flex gap-1 overflow-x-auto pb-1 lg:grid lg:gap-0.5 lg:overflow-visible" aria-label="Navigasi utama">
      {#each links as link}
        {@const Icon = link.icon}
        <a class:!bg-[#e8f2ed]={active === link.href} class:!font-bold={active === link.href} class:!text-[#145c3e]={active === link.href} class="group grid shrink-0 grid-cols-[1.1rem_auto] items-center gap-2 rounded-[.58rem] px-3 py-2.5 text-[.86rem] font-medium text-[#5d6c65] no-underline transition hover:bg-[#f0f5f2] hover:text-[#1c513c] active:translate-y-px lg:grid-cols-[1.25rem_1fr] lg:py-2.5" href={link.href} aria-current={active === link.href ? 'page' : undefined}>
          <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
          <span>{link.label}</span>
        </a>
      {/each}
    </nav>

    <div class="mt-auto hidden gap-2 border-t border-[#e7ece9] pt-4 lg:grid">
      <a class="grid grid-cols-[2rem_minmax(0,1fr)] items-center gap-2.5 rounded-[.6rem] p-1.5 text-inherit no-underline hover:bg-[#f0f5f2]" href="/account">
        <span class="grid size-8 place-items-center rounded-[.55rem] border border-[#d6e3dc] bg-[#eef5f1] text-[.75rem] font-extrabold text-[#176b49]" aria-hidden="true">{user?.display_name?.slice(0, 1).toUpperCase() || 'A'}</span>
        <span class="grid min-w-0 gap-0.5"><strong class="truncate text-[.78rem]">{user?.display_name}</strong><small class="truncate text-[.72rem] text-[#708078]">{user?.email}</small></span>
      </a>
      <button class="flex min-h-9 w-full items-center justify-start gap-2 rounded-[.55rem] border-0 bg-transparent px-2.5 py-2 text-left text-[.8rem] font-semibold text-[#67766f] hover:bg-[#f9eff0] hover:text-[#8d343f]" type="button" onclick={() => logoutDialog?.showModal()}><LogOut size={16} strokeWidth={1.8} aria-hidden="true" /><span>Keluar</span></button>
    </div>
  </aside>

  <main class="w-full max-w-[96rem] min-w-0 px-4 pb-16 pt-6 sm:px-5 lg:px-[clamp(1.25rem,3.3vw,3.5rem)] lg:pt-8">
    <header class="flex items-start justify-between gap-4 border-b border-[#e3e9e5] pb-5 sm:pb-7">
      <div><p class="mb-1 text-[.67rem] font-bold uppercase tracking-[.1em] text-[#65756d]">{eyebrow}</p><h1 class="m-0 text-[clamp(1.6rem,2.2vw,2rem)] font-bold leading-[1.15] tracking-[-.035em] text-[#15231d]">{title}</h1></div>
    </header>
    <slot />
  </main>
</div>

<dialog bind:this={logoutDialog} class="m-auto w-[min(92vw,26rem)] rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)] backdrop:bg-[#17241f]/35" aria-labelledby="logout-title">
  <div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4"><div><h2 id="logout-title" class="m-0 text-lg font-bold">Keluar dari dashboard?</h2><p class="mb-0 mt-1 text-sm text-[#66766f]">Sesi pada perangkat ini akan diakhiri.</p></div><button class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef] hover:text-[#263a30]" type="button" aria-label="Tutup dialog" onclick={() => logoutDialog?.close()} disabled={isLoggingOut}><X size={18} aria-hidden="true" /></button></div>
  <form class="flex justify-end gap-2 px-5 py-4" method="POST" action="?/logout" use:enhance={enhanceLogout}>
    <button class="secondary" type="button" onclick={() => logoutDialog?.close()} disabled={isLoggingOut}>Batal</button>
    <button class="danger" type="submit" disabled={isLoggingOut}>{isLoggingOut ? 'Keluar…' : 'Ya, keluar'}</button>
  </form>
</dialog>
