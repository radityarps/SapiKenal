<script lang="ts">
  import { ChevronDown, Check } from 'lucide-svelte';
  import { Select } from 'bits-ui';

  export let label: string;
  export let value = '';
  export let placeholder = 'Semua';
  export let items: { value: string; label: string }[] = [];
  export let onChange: (value: string) => void = () => {};

  let selectedValue = value || '__all__';

  function handleValueChange(next: string) {
    selectedValue = next;
    onChange(next === '__all__' ? '' : next);
  }

  $: if ((value || '__all__') !== selectedValue) selectedValue = value || '__all__';
</script>

<div class="grid gap-1.5 text-xs font-bold text-[#52635b]">
  <span>{label}</span>
  <Select.Root type="single" value={selectedValue} {items} onValueChange={handleValueChange}>
    <Select.Trigger class="flex min-h-10 w-full items-center justify-between gap-2 rounded-lg border border-[#cfdad4] bg-white px-3 py-2 text-left text-sm font-normal text-[#17241f] transition hover:border-[#aebfb6] focus-visible:border-[#4d8a6c] focus-visible:ring-4 focus-visible:ring-[#18794e]/10">
      <Select.Value {placeholder} />
      <ChevronDown size={16} strokeWidth={1.8} class="shrink-0 text-[#718078]" aria-hidden="true" />
    </Select.Trigger>
    <Select.Portal>
      <Select.Content class="z-50 max-h-72 min-w-[var(--bits-select-anchor-width)] overflow-hidden rounded-lg border border-[#d5e1db] bg-white p-1 text-[#17241f] shadow-[0_14px_30px_rgba(23,36,31,.14)]">
        <Select.Viewport>
          {#each items as item (item.value)}
            <Select.Item value={item.value} label={item.label} class="flex min-h-9 cursor-pointer items-center justify-between gap-3 rounded-md px-2.5 py-2 text-sm outline-none data-[highlighted]:bg-[#edf5f1] data-[highlighted]:text-[#145c3e]">
              {#snippet children({ selected })}
                <span>{item.label}</span>
                {#if selected}<Check size={15} strokeWidth={2} aria-hidden="true" />{/if}
              {/snippet}
            </Select.Item>
          {/each}
        </Select.Viewport>
      </Select.Content>
    </Select.Portal>
  </Select.Root>
</div>
