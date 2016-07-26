
#/bin/sh

rm ./_*sh
rm ./_*py

for e in ../blur/out*visualize; do rm $e; done
for e in ../blur/out*cpp; do rm $e; done
for e in ../blur/out*time.txt; do rm $e; done

for e in ../bilateral_grid/out*visualize; do rm $e; done
for e in ../bilateral_grid/out*cpp; do rm $e; done
for e in ../bilateral_grid/out*time.txt; do rm $e; done

for e in ../unsharp_mask_with_bilateral_grid/out*visualize; do rm $e; done
for e in ../unsharp_mask_with_bilateral_grid/out*cpp; do rm $e; done
for e in ../unsharp_mask_with_bilateral_grid/out*time.txt; do rm $e; done

for e in ../img_abstraction/out*visualize; do rm $e; done
for e in ../img_abstraction/out*cpp; do rm $e; done
for e in ../img_abstraction/out*time.txt; do rm $e; done


