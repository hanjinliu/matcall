function mlarr = bin_to_mlarray(path, shape, dtype)
    % path: str
    % shape: array
    % dtype: str
    %
    % >>> arr = bin_to_mlarray("/path/to/data.bin", [10, 20], "double");
    
    % TODO: For complex arrays, another function has to be defined.
    fp = fopen(path);
    try
        cls = str2func(dtype);
        mlarr = cls(fread(fp, dtype));
        if length(shape) > 1
            % MATLAB does not allow reshaping to a 1-D array.
            mlarr = reshape(mlarr, shape);
        end
    catch e
        fclose(fp);
        rethrow(e)
    end
    fclose(fp);
end