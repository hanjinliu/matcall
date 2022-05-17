function mlarr = bin_to_mlarray(path, shape, dtype)
    % path: str
    % shape: array
    % dtype: str
    %
    % >>> arr = bin_to_mlarray("/path/to/data.bin", [10, 20], "double");
    
    fp = fopen(path);
    try
        cls = str2func(dtype);
        mlarr_flat = cls(fread(fp, dtype));
        mlarr = reshape(mlarr_flat, shape);
    catch e
        fclose(fp);
        rethrow(e)
    end
    fclose(fp);
end