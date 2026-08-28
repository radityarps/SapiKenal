<script lang="ts">
  import { Pagination } from 'bits-ui';
  import { ChevronLeft, ChevronRight } from 'lucide-svelte';

  export let count = 0;
  export let page = 1;
  export let perPage = 25;
  export let onChange: (page: number) => void = () => {};

  function getPage() {
    return page;
  }

  function setPage(nextPage: number) {
    if (nextPage !== page) onChange(nextPage);
  }
</script>

{#if count > 0}
  <Pagination.Root {count} {perPage} bind:page={getPage, setPage} siblingCount={1} class="flex flex-wrap items-center justify-between gap-3 border-t border-[#e8edea] px-4 py-3">
    {#snippet children({ pages, range })}
      <p class="m-0 text-xs text-[#65756d]">Menampilkan {range.start}–{range.end} dari {count}</p>
      <div class="flex items-center gap-1" aria-label="Pagination">
        <Pagination.PrevButton class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#426353] hover:bg-[#edf5f1] hover:text-[#176b49] disabled:cursor-not-allowed disabled:opacity-40" aria-label="Halaman sebelumnya"><ChevronLeft size={17} strokeWidth={1.8} aria-hidden="true" /></Pagination.PrevButton>
        {#each pages as item (item.key)}
          {#if item.type === 'ellipsis'}
            <span class="grid size-8 place-items-center text-sm text-[#718078]" aria-hidden="true">…</span>
          {:else}
            <Pagination.Page page={item} class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-sm font-bold text-[#426353] hover:bg-[#edf5f1] data-[selected]:bg-[#176b49] data-[selected]:text-white">{item.value}</Pagination.Page>
          {/if}
        {/each}
        <Pagination.NextButton class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#426353] hover:bg-[#edf5f1] hover:text-[#176b49] disabled:cursor-not-allowed disabled:opacity-40" aria-label="Halaman berikutnya"><ChevronRight size={17} strokeWidth={1.8} aria-hidden="true" /></Pagination.NextButton>
      </div>
    {/snippet}
  </Pagination.Root>
{/if}
